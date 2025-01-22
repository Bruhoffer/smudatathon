import re

def clean_text(text):
    """
    Remove excessive spaces and normalize whitespace.
    """
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'\s+\n', '\n', text)  # Remove trailing spaces before newlines
    text = re.sub(r'\n\s+', '\n', text)  # Remove leading spaces after newlines
    return text.strip()

def preserve_headers(text):
    """
    Add consistent formatting to headers by adding newlines before and after.
    """
    headers = [
        "Allegation", "Background Information", "Investigative details",
        "Conclusions", "Recommendations"
    ]
    for header in headers:
        text = re.sub(fr'\b{header}\b', f'\n{header}:\n', text, flags=re.IGNORECASE)
    return text

def fix_numeric_formatting(text):
    """
    Standardize numeric values and fix broken numbers.
    """
    text = re.sub(r'€(\d+),(\d+)\s+0', r'€\1,\2', text)  # Fix broken euros
    text = re.sub(r'€(\d+),(\d+)\s+7\s+0', r'€\1,\2', text)  # Fix decimals
    text = re.sub(r'(\d+),(\d+)\s+and\s+Euro\s+(\d+),(\d+)', r'€\1,\2 and €\3,\4', text)  # Standardize Euro
    text = re.sub(r'Euro\s+(\d+),(\d+)', r'€\1,\2', text)  # Replace 'Euro' with €
    return text

def fix_missing_values(text):
    """
    Fix placeholders, missing values, and redundant words.
    """
    text = re.sub(r'Vendor\s+and\s+Vendor\s+', 'Vendor 1 and Vendor 2 ', text)  # Fix Vendor placeholders
    text = re.sub(r'\s+/\s+', '/', text)  # Fix slash-separated numbers
    text = re.sub(r'(?<=\d)/(?=\d)', r'/', text)  # Fix missing spaces in case numbers
    return text

def format_sections_and_lists(text):
    """
    Add newline before numbered lists and recommendations.
    """
    text = re.sub(r'(Recommendation \d+):', r'\n\1:\n', text)  # Format recommendations
    return text


def remove_extraneous_text(text):
    """
    Remove stray numbers, symbols, or redundant headers.
    """
    text = re.sub(r'\n\d+\n', '\n', text)  # Remove stray numbers between sections
    # Ensure no header is accidentally deleted; this is safer now
    text = re.sub(r'(Background Information:)\s+related to.*', r'\1', text)  # Fix incomplete sections
    return text

def finalize_text_for_tokenization(text):
    """
    Clean and preprocess the text for tokenization.
    """
    # Step-by-step cleaning process
    text = clean_text(text)
    text = preserve_headers(text)
    text = fix_numeric_formatting(text)
    text = fix_missing_values(text)
    text = format_sections_and_lists(text)
    text = remove_extraneous_text(text)
    return text

if __name__ == "__main__":
    # Read raw extracted text
    input_file = "../output/sample_extracted.txt"
    output_file = "../output/sample_tokenized_ready.txt"

    with open(input_file, "r") as f:
        raw_text = f.read()

    # Process the text
    tokenized_ready_text = finalize_text_for_tokenization(raw_text)

    # Save the processed output
    with open(output_file, "w") as f:
        f.write(tokenized_ready_text)

    print(f"Tokenization-ready text saved to {output_file}")
