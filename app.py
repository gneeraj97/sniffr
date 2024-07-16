from flask import Flask, render_template, request, redirect, url_for
import os
from run_gowitness import *
import scan

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        gui = request.form.get('gui') == 'on'
        client_name = request.form.get('client_name', 'specterops')
        gowitness_path = request.form.get('gowitness_path', 'gowitness')
        input_file_path = request.form.get('input_file_path', 'scan_urls.txt')
        screenshot_folder_name = request.form.get('screenshot_folder_name', 'screenshots')
        db_name = request.form.get('db_name', 'gowitness.sqlite3')
        extra_flags = request.form.get('extra_flags', '')
        gowitness_scan = request.form.get('gowitness_scan') == 'on'
        screenshot_path = request.form.get('screenshot_path', './gowitness/screenshots/')
        extension = request.form.get('extension', 'png')
        top_k = int(request.form.get('top_k', '10'))
        ner_model = request.form.get('ner_model', 'dslim/bert-base-NER')
        vlm_model = request.form.get('vlm_model', 'claude-3-5-sonnet-20240620')
        interesting_file = request.form.get('interesting_file', './utils/keywords.txt')
        dont_bother_file = request.form.get('dont_bother_file', './utils/dont_both_file.txt')
        api_key = request.form.get('api_key', '')
        
        current_directory = os.getcwd()
        
        if gowitness_scan:
            working_folder = os.path.join(current_directory, client_name, "gowitness").replace("\\", "/")
            os.makedirs(working_folder, exist_ok=True)
            
            output_dir = f"sqlite://{working_folder}/{db_name}"
            screenshot_dir = os.path.join(working_folder, screenshot_folder_name).replace("\\", "/")
            
            success, screenshot_path = get_screenshots(gowitness_path, input_file_path, output_dir, screenshot_dir, extra_flags)
        
        if success == 1:
            scan.get_top_vulnerable(
                screenshot_path if gowitness_scan else screenshot_path,
                extension,
                interesting_file,
                dont_bother_file,
                ner_model,
                vlm_model,
                api_key,
                top_k,
                client_name
            )
            message = f"Scan successful. Screenshots saved to {screenshot_path}."
        else:
            message = "There was some problem with GoWitness tool."
        
        return render_template('index.html', message=message)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
