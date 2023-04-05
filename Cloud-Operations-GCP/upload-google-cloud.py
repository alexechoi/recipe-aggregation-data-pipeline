import os
from google.cloud import storage

# If you are replicating you would need to change the keyfile details
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../Credentials/keyfile.json"

def upload_blob(bucket_name, source_file, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    with open(source_file, "rb") as f:
        blob.upload_from_file(f)

    print(f"File {source_file} uploaded to {destination_blob_name}.")

if __name__ == "__main__":
    output_dir = "../output"
    bucket_name = "achoi-data-eng-bucket"

    for file in os.listdir(output_dir):
        if file.endswith(".json"):
            file_path = os.path.join(output_dir, file)
            upload_blob(bucket_name, file_path, file)
