import subprocess
import argparse
import os

def get_screenshots(gowitness_path, input_file, output_dir, screenshot_path, extra_flags):
    
    if extra_flags == "":
        command = [gowitness_path, "file", "-f", input_file, "--screenshot-path", screenshot_path ,"-D", output_dir]
    else:
        command = [gowitness_path, "file", "-f", input_file,  extra_flags]
    success = 0
    try:
        print("GoWitness tool is starting.")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("GoWitness has done scaning the given URLs.")
        success = 1
    except subprocess.CalledProcessError as e:
        print(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        print("Error Output:\n", e.stderr)
    except FileNotFoundError:
        print(f"'{gowitness_path}' not found. Ensure it is installed and in your PATH.")
    
    return success, screenshot_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Required and optional arguments for running gowitness')
    parser.add_argument('--gowitness_path', type=str, default="gowitness",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--input_path', type=str, default="./scan_urls.txt",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--screenshot_folder_name', type=str, default="screenshots",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--db_name', type=str, default="gowitness.sqlite3",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--extra_flags', type=str, default="",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    parser.add_argument('--client_name', type=str, default="specterops",help='Path for your gowitness installation. Assumes that gowitness is added to the PATH.')
    
    args = parser.parse_args()
    
    current_directory = os.getcwd()
    working_folder = current_directory.replace("\\", "/") + "/" + args.client_name + "/gowitness/" 
    os.makedirs(working_folder, exist_ok=True)
    
    output_dir = "sqlite://" + working_folder + args.db_name
    screenshot_dir = working_folder + args.screenshot_folder_name
    
    get_screenshots(args.gowitness_path, 
                    args.input_path, 
                    output_dir,
                    screenshot_dir, 
                    args.extra_flags)
    
    
    