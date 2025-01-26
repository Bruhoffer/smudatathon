import pandas as pd
import spacy
import os

# Define paths
INPUT_CSV = "../src/structured_text_data.csv"
OUTPUT_CSV = "ner_output.csv"

# Define relevant entity labels
RELEVANT_LABELS = {
    "PERSON",  # People
    "ORG",     # Organizations
    "GPE",     # Geo-political entities (countries, cities, states)
    "DATE",    # Dates
    "LOC",     # Locations
    "NORP",    # Nationalities, religious or political groups
    "EVENT",   # Events
    "LAW",     # Laws, legal documents
    "FAC"      # Facilities (buildings, airports, etc.)
}

# Load spaCy's pre-trained model
def load_model():
    """Load the spaCy language model."""
    return spacy.load("en_core_web_md")

# Perform NER on a single text entry
def extract_entities(text, nlp):
    """
    Extract named entities from text using spaCy's NER.

    Args:
        text (str): Input text for entity extraction.
        nlp (Language): spaCy language model.

    Returns:
        list: List of entities with their text and labels.
    """
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    doc = nlp(text)
    entities = [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
        if ent.label_ in RELEVANT_LABELS  # Filter for relevant labels
    ]
    return entities

# Main processing function
def perform_ner(input_csv, output_csv):
    """
    Perform Named Entity Recognition on text data.

    Args:
        input_csv (str): Path to input CSV file.
        output_csv (str): Path to output CSV file.

    Returns:
        None
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    # Load dataset
    data = pd.read_csv(input_csv)

    # Initialize spaCy model
    nlp = load_model()

    # Apply NER to each row in the dataset
    print("Performing NER on the dataset...")
    data["entities"] = data["text"].apply(lambda text: extract_entities(text, nlp))

    # Save results to a CSV file
    data.to_csv(output_csv, index=False)
    print(f"NER results have been saved to {output_csv}.")

# Run the script
if __name__ == "__main__":
    perform_ner(INPUT_CSV, OUTPUT_CSV)