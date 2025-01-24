import pandas as pd
import json
import os

# Define paths to input files
excel_files = ["../data/news_excerpts_parsed.xlsx", "../data/wikileaks_parsed.xlsx"]
# Here i did it manually because i wanted to see if anything changes based on the jsons i input, but this can definitely be automated, left out 82.json to 108.json
json_files = ["../pdfsoutput/1.json", "../pdfsoutput/2.json", "../pdfsoutput/4.json", "../pdfsoutput/5.json", "../pdfsoutput/8.json", "../pdfsoutput/9.json", "../pdfsoutput/10.json", "../pdfsoutput/11.json",
              "../pdfsoutput/13.json", "../pdfsoutput/14.json", "../pdfsoutput/15.json", "../pdfsoutput/16.json", "../pdfsoutput/21.json", "../pdfsoutput/24.json", "../pdfsoutput/26.json", "../pdfsoutput/27.json",
              "../pdfsoutput/31.json", "../pdfsoutput/35.json", "../pdfsoutput/36.json", "../pdfsoutput/38.json", "../pdfsoutput/39.json", "../pdfsoutput/43.json", "../pdfsoutput/44.json", "../pdfsoutput/45.json",
              "../pdfsoutput/47.json", "../pdfsoutput/49.json", "../pdfsoutput/51.json", "../pdfsoutput/52.json", "../pdfsoutput/60.json", "../pdfsoutput/63.json", "../pdfsoutput/69.json", "../pdfsoutput/73.json",
              "../pdfsoutput/110.json", "../pdfsoutput/111.json", "../pdfsoutput/112.json", "../pdfsoutput/113.json"]

# Initialize a list to store structured data
structured_data = []

# Step 1: Extract text from Excel files
def extract_text_from_excel(file_path):
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        # Combine non-empty values and clean whitespace
        text = " ".join(map(str, row.dropna().values)).strip()
        if text:
            structured_data.append({"source": os.path.basename(file_path), "page": None, "text": text})

# Process all Excel files
for excel_file in excel_files:
    extract_text_from_excel(excel_file)

# Step 2: Extract and structure text from JSON files
def extract_text_from_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    if 'Blocks' in data:
        page_text = {}
        for block in data['Blocks']:
            if block.get('BlockType') == 'LINE' and 'Text' in block:
                page_number = block.get('Page', 1)  # Default to page 1 if not provided
                if page_number not in page_text:
                    page_text[page_number] = []
                page_text[page_number].append(block['Text'].strip())  # Clean individual lines

        # Combine lines into paragraphs for each page
        for page, lines in page_text.items():
            paragraph = " ".join(lines)
            structured_data.append({
                "source": os.path.basename(file_path),
                "page": page,
                "text": paragraph.strip()
            })

# Process all JSON files
for json_file in json_files:
    extract_text_from_json(json_file)

# Step 3: Remove noise and normalize text
def clean_text(text):
    text = text.replace("\n", " ").replace("\t", " ")  # Normalize newlines and tabs
    text = " ".join(text.split())  # Remove excessive whitespace
    return text

for entry in structured_data:
    entry["text"] = clean_text(entry["text"])

# Step 4: Save structured data to a CSV file
output_csv = "structured_text_data.csv"
pd.DataFrame(structured_data).to_csv(output_csv, index=False)

print(f"Structured text data has been saved to {output_csv}.")
