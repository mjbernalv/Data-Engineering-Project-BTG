# Proyecto Ingeniería de datos

Una compañía comercializadora de energía compra la electricidad a los generadores en el mercado mayoritario, donde después de una serie de contratos y control riesgos de precios esta se 
vende a los usuarios finales que pueden ser clientes residenciales, comerciales o industriales. El sistema de la compañía que administra este producto tiene la capacidad de exportar la 
información de proveedores, clientes y transacciones en archivos CSV.

Este proyecto crea una estrategia de datalake en S3 que permite cargar la información de los archivos CSV, realiza transformaciones básicas de los datos y los almacena en una zona procesada
utilizando AWS Glue, crea un proceso que detecta y cataloga automáticamente los esquemas de los datos almacenados en el datalake, y finalmente permite realizar consultas en SQL sobre los 
datos que han sido transformados utilizando Amazon Athena.

## Estructura del proyecto
A continuación se presenta la estructura general del proyecto.
``` bash
├── data/ # Archivos exportados del sistema
│ ├── clientes.csv
│ ├── proveedores.csv
│ └── transacciones.csv
├── glue_jobs/ # scripts de AWS Glue ETL
│ ├── catalog_data_glue.py
│ └── trasform_data_glue.py
├── scripts/ # Scripts de consultas y utilidad
│ └── athena_queries.py
└── upload_s3/ # Lógica para subir a S3
 └── upload_data_s3.py
```

## Pasos para la ejecución
A continuación se presentan los pasos que debes seguir para la ejecución de este proyecto.

### 1. Iniciar sesión en AWS
Inicia sesión con tu cuenta de AWS [aquí](https://aws.amazon.com/).

### 2. Crear bucket en Amazon S3
Dirígete a Amazon S3 y crea un nuevo bucket. Recuerda que el nombre debe ser único dentro del espacio de nombres global.

### 3. Configurar perfiles y claves de acceso
Abre Amazon Identity and Access Management (IAM) y crea un nuevo usuario. Agrega los siguientes permisos a este usuario:
- AmazonAthenaFullAccess
- AmazonS3FullAccess
- AWSLambdaBasicExecutionRole

Además, crea una clave de acceso para este usuario y obténÑ
- Access Key ID
- Secret Access Key

Estas credenciales serán necesarias para autenticarte con los servicios de AWS desde tus scripts de Python utilizando `boto3`.

### 4. Crea archivo con variables de ambiente
Dentro del proyecto crea un archivo llamado `.env` con la siguiente estructura:
``` bash
BUCKET_NAME=your_bucket_name
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=your_aws_region
```

### 5. Instalar librerías requeridas
Abre una terminal nueva y corre el comando `pip install -r requirements.txt` para instalar las librerías necesarias.

### 6. Subir archivos raw a Amazon S3
Los archivos que desees subir al bucket de S3 deben estar almacenados en la carpeta `data` y deben seguir la siguiente estructura:
- `clientes.csv`: contiene la información de los clientes con las columnas:
  - `tipo_identificacion`
  - `identificacion`
  - `nombre`
  - `ciudad`
- `proveedores.csv`: contiene la información de los proveedores con las columnas:
  - `nombre_proveedor`
  - `tipo_energia`
- `transacciones.csv`: contiene la información de las transacciones con las columnas:
  - `tipo_transaccion`
  - `nombre_entidad`
  - `cantidad_comprada`
  - `precio`
  - `tipo_energia`

Luego, corre el script `upload_s3/upload_data_s3.py` el cual se encarga de subir esta información en el bucket de S3 en la carpeta raw, que tiene la siguiente estructura:
``` bash
└── raw/ # Archivos exportados del sistema
  ├── clientes/
  │ └── load_date=YYYY-MM-DD/
  │   └── clientes.csv
  ├── proveedores/
  │ └── load_date=YYYY-MM-DD/
  │   └── proveedores.csv
  └── transacciones/
    └── load_date=YYYY-MM-DD/
      └── transacciones.csv
```


