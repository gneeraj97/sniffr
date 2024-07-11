import argparse
import datasets
from enum import Enum

def contains_words(input_string, word_file):
    input_string = input_string.lower()
    for word in word_file:
        if word in input_string:
            return True
    
    return False

def add_flag(img_file, word_file_path, dont_bother_file_path):
    
    img_file['dont_bother_flag'] = False
    img_file['interest_flag'] = False
    
    if contains_words(img_file['content'], dont_bother_file_path):
        img_file['dont_bother_flag'] = True
    
    if contains_words(img_file['content'], word_file_path):
        img_file['interest_flag'] = True
    
    return img_file

def main(input_file, word_file, dont_bother_file, output_file):
    dt = datasets.load_dataset('json', data_files=input_file, split="train")

    new = dt.map(lambda x: add_flag(x, word_file, dont_bother_file))

    new.to_json(output_file)

    print(f"Processing complete. Output saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON file and add interest flags based on keywords.")
    parser.add_argument("input_file", help="Path to the input JSON file")
    parser.add_argument("word_file", help="Path to the file containing keywords") # If input_file contains anything word from wordlist, add the True flag
    parser.add_argument("dont_bother_file", help="Path to the file containing keywords that we dont wanna bother")
    parser.add_argument("output_file", help="Path to save the output JSON file")
    
    args = parser.parse_args()

    main(args.input_file, args.word_file, args.dont_bother_file, args.output_file)
