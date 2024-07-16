import argparse
import os
from run_gowitness import *
import scan


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Required and optional arguments for running gowitness')
    
    # Overall flags
    parser.add_argument('--gui', type=bool, default=False, help='Your Anthropic key')
    parser.add_argument('--client_name', type=str, default="specterops",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    
    # Go witness arguments
    parser.add_argument('--gowitness_path', type=str, default="gowitness",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--input_file_path', type=str, default="scan_urls.txt",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--screenshot_folder_name', type=str, default="screenshots",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--db_name', type=str, default="gowitness.sqlite3",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--extra_flags', type=str, default="",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--gowitness_scan', type=bool, default=True, help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    
    # Attackability score
    parser.add_argument('--screenshot_path', type=str, default='./gowitness/screenshots/',help='The directory to search in.')
    parser.add_argument('--extension', type=str, default='png',help='The file extension to search for.')
    parser.add_argument('--top_k', type=int, default='10',help='To return the top k results')
    parser.add_argument('--ner_model', type=str, default='dslim/bert-base-NER',help='Entity recognition model')
    parser.add_argument('--vlm_model', type=str, default='claude-3-5-sonnet-20240620',help='The visual language model')
    parser.add_argument('--interesting_file', type=str, default='./utils/keywords.txt',help='The interesting keyword file path')
    parser.add_argument('--dont_bother_file', type=str, default='./utils/dont_both_file.txt',help='The dont bother keyword file path')
    parser.add_argument('--api_key', type=str,help='Your Anthropic key')
    
    
    args = parser.parse_args()
    
    current_directory = os.getcwd()
    
    if args.gowitness_scan:
        working_folder = current_directory.replace("\\", "/") + "/" + args.client_name + "/gowitness/" 
        os.makedirs(working_folder, exist_ok=True)
        
        output_dir = "sqlite://" + working_folder + args.db_name
        screenshot_dir = working_folder + args.screenshot_folder_name
        
        success, screenshot_path = get_screenshots(args.gowitness_path, 
                                                    args.input_file_path, 
                                                    output_dir,
                                                    screenshot_dir, 
                                                    args.extra_flags)
    print(screenshot_path)
    if success==1:    
        scan.get_top_vulnerable(screenshot_path if args.gowitness_scan else args.screenshot_path, 
                        args.extension, 
                        args.interesting_file, 
                        args.dont_bother_file, 
                        args.ner_model, 
                        args.vlm_model, 
                        args.api_key, 
                        args.top_k,
                        args.client_name)
    else:
        print("There was some problem with GoWitness tool.")
    