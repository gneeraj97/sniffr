# Sniffr

Sniffr is a network analysis tool designed to capture, filter, and analyze screenshots of clients domains while doing penetration testing. It provides a simple way of identifying potential vulnerabilities of domains and provides attackability scores. It reduces the time taken to go through 1000s of gowitness screenshots from a few days manually to a hour or two. It filters and gives you top-k (k of your choice) attackable domains out of 1000s of domains, along with the information on the kind of services hosted on that domain. 

## Features

- Real-time screenshot capture by gowitness tool
- Uses OCR, entity recognition to focus on important parts of the screenshots
- Employ VLM (Visual Language Model), Anthropic's, to analyse and describe the services on web domain

## Installation

To install Sniffr, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gneeraj97/sniffr.git
   ```

2. **Navigate to the project directory:**

   ```bash
   cd sniffr
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting Sniffr

To start Sniffr and begin capturing and analysing screenshots, use the `run_sniffr.py` script. This script provides various options for configuring the screenshots capture process. There is a graphical interface for this tool, app.py. This is a simple web interface made on Flask for easy configuration of arguments.  

```bash
python run_sniffr.py
```
or 

```bash
python app.py
```

### Configuration

Sniffr can be configured using command-line arguments. The main configuration options include:

- **`--screenshot_path`**: The directory to save screenshots (default: `./gowitness/screenshots/`).
- **`--extension`**: The file extension to search for (default: `png`).
- **`--top`**: Number of top results to return (default: 10).
- **`--ner_model`**: Entity recognition model (default: `dslim/bert-base-NER`).
- **`--vlm_model`**: Visual language model (default: `claude-3-5-sonnet-20240620`).
- **`--interesting_file`**: Path to the interesting keywords file (default: `./utils/keywords.txt`).
- **`--dont_bother_file`**: Path to the "don't bother" keywords file (default: `./utils/dont_both_file.txt`).
- **`--key`**: Your Anthropic API key.
- **`--client_name`**: Name of the client for which the scan is performed (default: `specterops`).

### Example Commands

- **Capture packets and save screenshots:**

  ```bash
  python run_sniffr.py --screenshot_path ./gowitness/screenshots/ --extension png --top 10 --ner_model dslim/bert-base-NER --vlm_model claude-3-5-sonnet-20240620 --interesting_file ./utils/keywords.txt --dont_bother_file ./utils/dont_both_file.txt --key YOUR_API_KEY --client_name specterops
  ```

## Overall structure of the code

- Reads and processes screenshots from the specified directory.
- Uses the provided NER and VLM models to analyze the content of the images.
- Filters results based on keywords of interest and those to ignore.
- Ranks the images based on their vulnerability scores.
- Outputs the top k results to CSV and JSON files for further analysis.
- You can change the name of client and it will create a separate folder for the client to keep the analysis separate and clean.

## Contributing

Contributions are welcome! If you find a bug or want to add a new feature, feel free to submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
