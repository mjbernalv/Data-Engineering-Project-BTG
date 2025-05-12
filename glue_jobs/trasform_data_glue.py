import sys
import boto3
import datetime as dt
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.utils import getResolvedOptions
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.types import *
from pyspark.sql import functions as F

# Parámetros
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'BUCKET_NAME'])
BUCKET_NAME = args['BUCKET_NAME']
LOAD_DATE = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')

# Inicializar Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


def transformations(df):
    # Transformación 1: Estandarizar tipo de documento
    if "tipo_documento" in df.columns:
        df = df.withColumn("tipo_documento", F.upper(F.col("tipo_documento")))

    # Transformación 2: Estandarizar identificación
    if "identificacion" in df.columns:
        df = df.withColumn("identificacion", F.regexp_replace(F.col("identificacion"), "-", ""))

    # Transformación 3: Estandarizar tipo de energía y tipo de transacción
    if "tipo_energia" in df.columns:
        df = df.withColumn("tipo_energia", F.lower(F.col("tipo_energia")))
    if "tipo_transaccion" in df.columns:
        df = df.withColumn("tipo_transaccion", F.lower(F.col("tipo_transaccion")))

    # Transformación 4: cantidad_comprada y precio como float
    if "cantidad_comprada" in df.columns:
        df = df.withColumn("cantidad_comprada", F.col("cantidad_comprada").cast("float"))
    if "precio" in df.columns:
        df = df.withColumn("precio", F.col("precio").cast("float"))

    return df

def transform_data():
    files = ['clientes', 'proveedores', 'transacciones']
    
    for entity_name in files:
        # Eliminar archivos existentes en la carpeta de fecha de carga
        s3_client = boto3.client('s3')
        existing_files = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=f"staged/load_date={LOAD_DATE}/"
        )
        if 'Contents' in existing_files:
            for obj in existing_files['Contents']:
                s3_client.delete_object(
                    Bucket=BUCKET_NAME,
                    Key=obj['Key']
                )

        # Leer datos de la capa raw
        file_path = f"s3://{BUCKET_NAME}/raw/{entity_name}/load_date={LOAD_DATE}/{entity_name}.csv"
        
        # Crear DynamicFrame de los datos fuente
        dyf = glueContext.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={"paths": [file_path]},
            format="csv",
            format_options={
                "withHeader": True,
                "separator": ","
            }
        )
        
        # Convertir a DataFrame para realizar transformaciones
        df = dyf.toDF()
        
        # Aplicar transformaciones específicas
        df = transformations(df).coalesce(1)
        
        # Convertir de vuelta a DynamicFrame
        transformed_dyf = DynamicFrame.fromDF(df, glueContext, f"{entity_name}_staged")

        # Escribir a un directorio temporal primero
        temp_path = f"s3://{BUCKET_NAME}/temp/{entity_name}_{LOAD_DATE}"
    
        glueContext.write_dynamic_frame.from_options(
            frame=transformed_dyf,
            connection_type="s3",
            connection_options={"path": temp_path},
            format="parquet",
            format_options={"compression": "none"}
        )
    
        # Guardar archivo parquet
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"temp/{entity_name}_{LOAD_DATE}"
        )
            
        parquet_file = None
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.parquet'):
                parquet_file = obj['Key']
                break
        
        if parquet_file:
            dest_key = f"staged/{entity_name}/load_date={LOAD_DATE}/{entity_name}.parquet"
            s3_client.copy_object(
                Bucket=BUCKET_NAME,
                CopySource={'Bucket': BUCKET_NAME, 'Key': parquet_file},
                Key=dest_key
            )
            for obj in response.get('Contents', []):
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])

transform_data()
job.commit()
