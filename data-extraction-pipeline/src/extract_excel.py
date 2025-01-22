import pandas as pd

def extract_excel_data(file_path):
    df = pd.read_excel(file_path)
    return df

if __name__ == "__main__":
    excel_path = "../data/news_excerpts_parsed.xlsx"
    data = extract_excel_data(excel_path)
    data.to_csv("../output/sample_extracted.csv", index=False)
