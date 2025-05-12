import os
import boto3
import pandas as pd
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()
AWS_REGION = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('BUCKET_NAME')
DATABASE_NAME = os.getenv('DATABASE_NAME')

def query_with_athena(database_name, table_name, query=None):
    # Crear una sesión con credenciales
    session = boto3.Session(region_name=AWS_REGION)
    
    # Crear cliente de Athena
    athena_client = session.client('athena')

    try:
        response = athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={
                    'Database': database_name
                },
                ResultConfiguration={
                'OutputLocation': f"s3://{BUCKET_NAME}/athena/query-results/",
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Esperar a que la consulta se complete
        state = 'RUNNING'
        while state in ['RUNNING', 'QUEUED']:
            time.sleep(1)
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            state = response['QueryExecution']['Status']['State']
            
            if state == 'FAILED':
                error_message = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                raise Exception(f"Query failed: {error_message}")
            elif state == 'CANCELLED':
                raise Exception("Query was cancelled")
        
        # Obtener los resultados
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        
        # Procesar los resultados en un DataFrame de pandas
        columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        data = []
        for row in results['ResultSet']['Rows'][1:]:  # Skip the header row
            data.append([field.get('VarCharValue', '') for field in row['Data']])
        
        df = pd.DataFrame(data, columns=columns)
    except Exception as e:
        print(f"Error: {e}")
        df = pd.DataFrame()
        
    return df

if __name__ == "__main__":
    # Query 1: Clientes con tipo de identificación CC
    print("Query 1: Clientes con tipo de identificación CC")
    query1 = """SELECT * 
                FROM clientes 
                WHERE tipo_identificacion = 'CC'"""
    df1 = query_with_athena(DATABASE_NAME, 'clientes', query1)
    print(df1)
    print()

    # Query 2: Transacciones con precio total pagado
    print("Query 2: Transacciones con precio total pagado")
    query2 = """SELECT tipo_transaccion,
                       nombre_entidad, 
                       cantidad_comprada,
                       precio,
                       cantidad_comprada * precio as total_pagado
                FROM transacciones
    """
    df2 = query_with_athena(DATABASE_NAME, 'transacciones', query2)
    print(df2)
    print()

    # Query 3: Transacciones de venta con información de clientes
    print("Query 3: Transacciones de venta con información de clientes")
    query3 = """SELECT 
                    t.nombre_entidad,
                    c.tipo_identificacion,
                    c.identificacion,
                    c.ciudad,
                    t.tipo_energia
                FROM transacciones t
                JOIN clientes c ON t.nombre_entidad = c.nombre
                WHERE t.tipo_transaccion = 'venta'"""
    df3 = query_with_athena(DATABASE_NAME, 'transacciones', query3)
    print(df3)
    print()