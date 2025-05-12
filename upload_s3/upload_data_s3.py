import os
import boto3
import datetime as dt
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Setup AWS
BUCKET_NAME = os.getenv('BUCKET_NAME')

# Fecha de carga
LOAD_DATE = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')

# Inicializar cliente de S3
s3 = boto3.client('s3')

def upload_file_to_s3(folder_path, bucket_name, base_s3_path = 'raw'):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(file_path) and file_name.endswith('.csv'):
            entity_name = file_name.split('.')[0]
            if not any(key in file_name.lower() for key in ['proveedores', 'clientes', 'transacciones']):
                print(f"Skipping {file_name}: not a recognized category")
                continue

            s3_key = f"{base_s3_path}/{entity_name}/load_date={LOAD_DATE}/{file_name}"
            try:
                s3.upload_file(file_path, bucket_name, s3_key)
                print(f"Uploaded {file_name} to s3://{bucket_name}/{s3_key}")
            except Exception as e:
                print(f"Failed to upload {file_name}: {e}")

if __name__ == "__main__":
    folder_path = 'data'
    upload_file_to_s3(folder_path, BUCKET_NAME)