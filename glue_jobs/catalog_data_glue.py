import boto3
import sys
import time
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import datetime as dt

# Parámetros
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'BUCKET_NAME', 'DATABASE_NAME', 'IAM_ROLE'])
BUCKET_NAME = args['BUCKET_NAME']
DATABASE_NAME = args['DATABASE_NAME']
IAM_ROLE = args['ROLE']
LOAD_DATE = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')

# Inicializar Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Crear cliente de Glue
glue_client = boto3.client('glue')

# Crear crawler para descubrir y catalogar los datos
crawler_name = f"{args['JOB_NAME']}_crawler"

# Revisar si el crawler ya existe
try:
    response = glue_client.get_crawler(Name=crawler_name)
    print(f"Crawler {crawler_name} already exists")
except glue_client.exceptions.EntityNotFoundException:
    # Crear un nuevo crawler si no existe
    response = glue_client.create_crawler(
        Name=crawler_name,
        Role=IAM_ROLE,
        DatabaseName=DATABASE_NAME,
        Targets={
            'S3Targets': [
                {
                    'Path': BUCKET_NAME
                }
            ]
        },
        SchemaChangePolicy={
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'DELETE_FROM_DATABASE'
        },
        Configuration='{\"Version\":1.0,\"CrawlerOutput\":{\"Partitions\":{\"AddOrUpdateBehavior\":\"InheritFromTable\"},\"Tables\":{\"AddOrUpdateBehavior\":\"MergeNewColumns\"}}}'
    )
    print(f"Created crawler {crawler_name}")

# Comenzar el crawler
glue_client.start_crawler(Name=crawler_name)

crawler_state = glue_client.get_crawler(Name=crawler_name)['Crawler']['State']
while crawler_state in ['RUNNING', 'STOPPING']:
    print(f"Crawler is {crawler_state}. Waiting...")
    time.sleep(30)
    crawler_state = glue_client.get_crawler(Name=crawler_name)['Crawler']['State']

job.commit()