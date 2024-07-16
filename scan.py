import os
import argparse
import easyocr
from utils import domain_flagger, scorer
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from anthropic import Anthropic
import base64
import xml.etree.ElementTree as ET
import re
import datasets
import warnings
warnings.filterwarnings("ignore")


def init_vlm(key):
    client = Anthropic(api_key=key)
    return client

def read_screenshots(path, ext):
    files = []
    for file in os.listdir(path):
        if file.endswith(ext):
            files.append(file)
    return files

def extract_text_from_image(image_path):
    reader = easyocr.Reader(['en'])  # Specify the languages you want to support
    results = reader.readtext(image_path)
    if results == []:
        return "--BLANK--" 
    tmp = ''
    for res in results:
        tmp += str(res[1])
    return tmp

def init_ner_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code = True)
    model = AutoModelForTokenClassification.from_pretrained(model_name, trust_remote_code = True, device_map = "cuda")

    nlp = pipeline("ner", model=model, tokenizer=tokenizer)
    return model, tokenizer, nlp
    
def get_full_word(text, start):
    # Use regex to find the full word in the text
    match = re.search(r'\b\w+\b', text[start:])
    if match:
        return match.group(0)
    return ""

def get_entities(content, pipe):
    
    example = content

    ner_results = pipe(example)
    # return ner_results
    entities = []
    entity = ""
    entity_label = ""
    entity_start = 0
    entity_end = 0

    for i, result in enumerate(ner_results):
        if result['entity'].startswith("B-"):
            if entity:
                entities.append({
                    "entity": entity_label,
                    "score": score,
                    "word": entity,
                    "start": entity_start,
                    "end": entity_end
                })
            entity = result['word']
            entity_label = result['entity'][2:]
            entity_start = result['start']
            entity_end = result['end']
            score = result['score']
        elif result['entity'].startswith("I-") and result['entity'][2:] == entity_label:
            entity += result['word'].replace("##", "")
            entity_end = result['end']
            score = min(score, result['score'])
        else:
            if entity:
                entities.append({
                    "entity": entity_label,
                    "score": score,
                    "word": entity,
                    "start": entity_start,
                    "end": entity_end
                })
                entity = ""
                entity_label = ""
                entity_start = 0
                entity_end = 0
                score = 0

    if entity:
        entities.append({
            "entity": entity_label,
            "score": score,
            "word": entity,
            "start": entity_start,
            "end": entity_end
        })

    # Ensure full words for ORG and MISC entities
    prob_entities_misc_and_org = []
    for ent in entities:
        if ent['entity'] in ["ORG", "MISC"]:
            full_word = get_full_word(example, ent['start'])
            if full_word.lower().startswith(ent['word'].lower()):
                ent['word'] = full_word
                ent['end'] = ent['start'] + len(full_word)
                prob_entities_misc_and_org.append(full_word)

    return list(set(prob_entities_misc_and_org))

def parse_response(response):
    response_with_root = f"<root>{response}</root>"
    try:
        root = ET.fromstring(response_with_root)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return [], None
    
    entities = []
    try:
        for entity in root.findall('.//entity'):
            name = entity.attrib['name']
            description = entity.text.strip()
            entities.append((name, description))
    except Exception as e:
        print(f"Error extracting entities: {e}")
    
    score = None
    try:
        score_element = root.find('.//Score')
        if score_element is not None:
            score = int(score_element.text.strip())
    except Exception as e:
        print(f"Error extracting score: {e}")
    
    txt = ''
    for ent in entities:
        txt += " ==> ".join(ent) + "\n"
    
    return txt, score

def get_analysis_and_vlm_score(rw, prompt, client,directory, MODEL_NAME):
    with open(directory + rw["image_path"], "rb") as image_file:
        binary_data = image_file.read()
        base_64_encoded_data = base64.b64encode(binary_data)
        base64_string = base_64_encoded_data.decode('utf-8')
        
    message_list = [
        {
            "role": 'user',
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64_string}},
                {"type": "text", "text": prompt.format(list_entity = str(rw["entities"]))}
            ]
        }
    ]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2048,
        messages=message_list
    )
    entities, score = parse_response(response.content[0].text)
    rw["analysis"] = entities
    rw["score_vlm"] = score
    return rw

def dataset_filter_function(example):
    return (example["content"] != "--BLANK--") and ((example["dont_bother_flag"] == False) and (example["interest_flag"] == True)) # Modify this condition as needed

def avg_scorer(rw):
    keyword_score = rw.get("keyword_score", 40) 
    missing_score = rw.get("missing_score", 40)
    rw['avg_score'] = (keyword_score + missing_score)/2
    
    return rw

def printing_function(top_k_instances):
    print("S.no | Image name | Analysis | Attackability Score")
    print("-"*100)
    for idx, instance in enumerate(top_k_instances):
        print(f"{idx+1} | {instance['image_path']} | {instance['analysis']} | {instance['avg_score']}")
        print("-"*100)
        print("\n")

def no_analysis(j):
    if j['analysis'] == "":
        j['analysis'] = "No Analysis"
    return j

def get_top_vulnerable(screenshot_path, extension, interesting_file, dont_bother_file, ner_model, vlm_model, api_key, top_k, client_name):
    
    screenshot_path = screenshot_path + "/"
    print('Reading screenshot file names')
    screenshots = read_screenshots(screenshot_path, extension)
    screenshots_data = [{"image_path": path} for path in screenshots]
    screenshots_data = datasets.Dataset.from_list(screenshots_data)
    print(f"Total screenshots: {len(screenshots_data)}")
    
    print('Extracting and saving content from the images using OCR.')
    ocr = screenshots_data.map(lambda x: {"content": extract_text_from_image(screenshot_path + "/" + x['image_path'])})
    ocr.to_csv(f"./{client_name}/output/OCR_extraction/All_ocr_extracted.csv")
    ocr.to_json(f"./{client_name}/output/OCR_extraction/All_ocr_extracted.json")
    print('Content extraction from the images completed.')
    
    print('Filtering on the interesting and don\'t bother flags.')
    interesting = scorer.load_keywords(interesting_file)
    dont_bother = scorer.load_keywords(dont_bother_file)
    
    flagged_ocr = ocr.map(lambda y: domain_flagger.add_flag(y, interesting ,dont_bother))
    filetered_ocr = flagged_ocr.filter(dataset_filter_function)
    print(f"Total screenshots: {len(filetered_ocr)}")
    print(f'Total reduction in dataset: {round((1 - len(filetered_ocr)/len(screenshots_data))*100,2)}%')
    
    ## Get keyword score
    print('Calculating keyword score.')
    keyword_scored_ocr = filetered_ocr.map(lambda z: {"keyword_score": scorer.calculate_score(z["content"], interesting, dont_bother)})
    
    ## Entity recognition
    print('Entity recognition started.')
    model, tokenizer, nlp_pipe = init_ner_model(ner_model)
    entitiy_ocr = keyword_scored_ocr.map(lambda x: {"entities": get_entities(x["content"], nlp_pipe)})
    entitiy_ocr.to_json(f"./{client_name}/output/entities/entity_ocr.json")
    entitiy_ocr.to_csv(f"./{client_name}/output/entities/entity_ocr.csv")
    
    
    ## Analysing the webpage
    print('Image analysis and vlm attackability score calculation by anthropic started.')
    prompt = '''You will be given an image and a list of entities present in that image. Your task is to analyze these entities and determine if they are related to any of the following categories:

    1. Access management
    2. Authentication
    3. IoT devices (Like printers)
    4. Password management
    5. Network security
    6. Data encryption
    7. Cloud services
    8. Cybersecurity software

    Image is attached with the 

    And here is the list of entities present in the image:
    <entity_list>
    {{ list_entity }}
    </entity_list>

    Analyze each entity in the list and determine if it is related to any of the categories mentioned above. Consider the entity name, its potential usage in the context of the image, and your knowledge of the related services and software.

    For each relevant entity, write a brief description explaining how it relates to one or more of the categories. Your description should incorporate:
    1. The name of the entity
    2. Its potential function or purpose in the image
    3. How it relates to the relevant category(ies)
    4. Any additional insights based on the image context and your knowledge of the technology and version

    If an entity does not clearly relate to any of the categories, you may omit it from your response. Similarly if an entity related to the categories is not listed but is present in the image, use it. Finally, give a score out of 100 based on how interesting the photo is based on these criterias:
    1. Old looking websites == More interesting
    2. Login pages == More interesting
    3. 404 pages == Less interesting
    4. Parked domain == Less interesting
    5. Upload feature == More interesting 

    Present your analysis in the following format:

    <analysis>
    <entity name="[Entity Name]">
    [Your brief description of the entity and its relevance to the categories]
    </entity>

    [Repeat for each relevant entity]
    </analysis>
    <Score>[Score]</Score>

    Remember to base your analysis on the information provided in the image description, the entity names, and your knowledge of the related technologies and services. Do not invent or assume information that is not implied by the given context. Be crisp in your reply. Do not explain how you arrive at the score.'''
    
    
    client = init_vlm(api_key)
    analysis_ocr_vlm = entitiy_ocr.map(lambda x: get_analysis_and_vlm_score(x, prompt, client, screenshot_path,vlm_model))
    analysis_ocr_vlm.to_csv(f"./{client_name}/output/vlm/analysis_ocr_vlm.csv")
    analysis_ocr_vlm.to_json(f"./{client_name}/output/vlm/analysis_ocr_vlm.json")
    
    ## Find the average attackability score
    print('Calculating the average score')
    average_score_ocr_vlm = analysis_ocr_vlm.map(avg_scorer)
    average_score_ocr_vlm = average_score_ocr_vlm.sort("avg_score", reverse = True)
    average_score_ocr_vlm_cleaned = average_score_ocr_vlm.map(no_analysis)
    average_score_ocr_vlm_cleaned.to_csv(f"./{client_name}/results/All_attack_portals_scored.csv")
    average_score_ocr_vlm_cleaned.to_json(f"./{client_name}/results/All_attack_portals_scored.json")
    
    top_k_instances = average_score_ocr_vlm_cleaned.select(range(min(top_k, len(average_score_ocr_vlm_cleaned))))
    ## save and print the information to a CSV format
    
    printing_function(top_k_instances)
    top_k_instances.to_csv(f"./{client_name}/results/Best_possible_attack_portals.csv")
    top_k_instances.to_json(f"./{client_name}/results/Best_possible_attacks.json")

    
if __name__ == "__main__":

    print('Reading arguments.')
    
    parser = argparse.ArgumentParser(description='List files with a specific extension in a directory.')
    parser.add_argument('--screenshot_path', type=str, default='./gowitness/screenshots/',help='The directory to search in.')
    parser.add_argument('--extension', type=str, default='png',help='The file extension to search for.')
    parser.add_argument('--top', type=int, default='10',help='To return the top k results')
    parser.add_argument('--ner_model', type=str, default='dslim/bert-base-NER',help='Entity recognition model')
    parser.add_argument('--vlm_model', type=str, default='claude-3-5-sonnet-20240620',help='The visual language model')
    parser.add_argument('--interesting_file', type=str, default='./utils/keywords.txt',help='The interesting keyword file path')
    parser.add_argument('--dont_bother_file', type=str, default='./utils/dont_both_file.txt',help='The dont bother keyword file path')
    parser.add_argument('--key', type=str, help='Your Anthropic key')
    parser.add_argument('--client_name', type=str, default="specterops",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    
    args = parser.parse_args()

    get_top_vulnerable(args.screenshot_path, 
                       args.extension, 
                       args.interesting_file, 
                       args.dont_bother_file, 
                       args.ner_model, 
                       args.vlm_model, 
                       args.key, 
                       args.top,
                       args.client_name)    
