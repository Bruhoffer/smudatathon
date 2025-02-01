import boto3
import os
import json
import time

def start_textract_analysis(file_path, bucket_name, object_name, feature_types):
    """
    Start an asynchronous Textract job for document analysis.
    """
    textract = boto3.client('textract', region_name="ap-southeast-2")
    response = textract.start_document_analysis(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_name
            }
        },
        FeatureTypes=feature_types
    )
    return response['JobId']

def start_textract_text_detection(file_path, bucket_name, object_name):
    """
    Start an asynchronous Textract job for text detection.
    """
    textract = boto3.client('textract', region_name="ap-southeast-2")
    response = textract.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_name
            }
        }
    )
    return response['JobId']

def check_job_status(job_id):
    """
    Poll the status of an asynchronous Textract job with enhanced error handling.
    """
    textract = boto3.client('textract', region_name="ap-southeast-2")
    while True:
        try:
            response = textract.get_document_analysis(JobId=job_id)
            status = response['JobStatus']
            print(f"Job {job_id} status: {status}")
            
            if status in ['SUCCEEDED', 'FAILED']:
                return status
            print("Waiting for job to complete...")
        except Exception as e:
            print(f"Error checking job status for JobId {job_id}: {e}")
            raise
        
        time.sleep(5)

def get_textract_results(job_id):
    """
    Retrieve the results of a completed Textract job.
    """
    textract = boto3.client('textract', region_name="ap-southeast-2")
    response = textract.get_document_analysis(JobId=job_id)
    return response

def process_pdf_with_async_textract(file_path, output_folder, bucket_name):
    """
    Upload the PDF to S3 and process it using asynchronous Textract APIs.
    """
    s3 = boto3.client('s3', region_name="ap-southeast-2")

    # Upload the file to S3
    object_name = os.path.basename(file_path)
    try:
        s3.upload_file(file_path, bucket_name, object_name)
    except Exception as e:
        print(f"Failed to upload {file_path} to bucket {bucket_name}: {e}")
        return

    try:
        print(f"Starting document analysis for {file_path}...")
        job_id = start_textract_analysis(file_path, bucket_name, object_name, ["FORMS", "TABLES"])
    except Exception as e:
        print(f"AnalyzeDocument failed for {file_path}, falling back to text detection: {e}")
        try:
            job_id = start_textract_text_detection(file_path, bucket_name, object_name)
        except Exception as fallback_error:
            print(f"Failed to start text detection for {file_path}: {fallback_error}")
            return

    try:
        status = check_job_status(job_id)
    except Exception as status_error:
        print(f"Error while checking job status for {file_path}: {status_error}")
        return

    if status == 'SUCCEEDED':
        try:
            results = get_textract_results(job_id)

            output_file = os.path.join(output_folder, os.path.basename(file_path).replace(".pdf", ".json"))
            with open(output_file, "w") as f:
                json.dump(results, f, indent=4)

            print(f"Processed {file_path} and saved output to {output_file}")
        except Exception as results_error:
            print(f"Failed to retrieve or save results for {file_path}: {results_error}")
    else:
        print(f"Textract job failed for {file_path}")

def process_multiple_pdfs(input_folder, output_folder, bucket_name):
    """
    Process all PDFs in the input folder using AWS Textract.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(input_folder, file_name)
            print(f"Processing file: {file_path}")
            process_pdf_with_async_textract(file_path, output_folder, bucket_name)

if __name__ == "__main__":
    # Define input and output folders and S3 bucket name
    input_folder = "../../pdfs"
    output_folder = "../../pdfsoutput"
    bucket_name = "smudatathon-textract-bucket" 

    process_multiple_pdfs(input_folder, output_folder, bucket_name)
