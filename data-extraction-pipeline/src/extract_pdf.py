import pdfplumber

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages])

if __name__ == "__main__":
    pdf_path = "/Users/justiny/Projects/smudatathon/data-extraction-pipeline/data/1.pdf"
    text = extract_text_from_pdf(pdf_path)
    with open("../output/sample_extracted.txt", "w") as f:
        f.write(text)
