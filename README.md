# Proyecto Ingeniería de datos
#### Por: María José Bernal Vélez

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
│ └── transform_data_glue.py
├── iac/ # Terraform infrastructure as code
│ ├── iam_roles.tf
│ ├── main.tf
│ ├── outputs.tf
│ ├── terraform.tfvars
│ └── variables.tf
├── scripts/ # Scripts de consultas y utilidad
│ └── athena_queries.py
└── upload_s3/ # Lógica para subir a S3
 └── upload_data_s3.py
```

## Pasos para la ejecución
Los pasos que debes seguir para la ejecución de este proyecto son los siguientes.

### 1. Iniciar sesión en AWS
Inicia sesión con tu cuenta de AWS [aquí](https://aws.amazon.com/).

### 2. Crear bucket en Amazon S3
Dirígete a [Amazon S3](https://aws.amazon.com/es/s3/) y crea un nuevo bucket. Recuerda que el nombre debe ser único dentro del espacio de nombres global.

### 3. Configurar perfiles y claves de acceso
Abre [AWS Identity and Access Management (IAM)](https://aws.amazon.com/es/iam/) y crea un nuevo usuario. Agrega los siguientes permisos a este usuario:
- AmazonAthenaFullAccess
- AmazonS3FullAccess
- CloudWatchLogsFullAccess

Además, crea una clave de acceso para este usuario y obtén:
- Access Key ID
- Secret Access Key

Estas credenciales serán necesarias para autenticarte con los servicios de AWS desde tus scripts de Python utilizando `boto3`.

Adicionalmente, debes crear un rol (`glue_role`) que tenga los siguientes permisos para las tareas de AWS Glue:
- AmazonAthenaFullAccess
- AWSGlueConsoleFullAccess
- AmazonS3FullAccess

### 4. Crear archivo con variables de entorno
Dentro del proyecto crea un archivo llamado `.env` con la siguiente estructura:
``` bash
BUCKET_NAME=your_bucket_name
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=your_aws_region
```
**Importante:** El archivo .env contiene credenciales sensibles (como claves de acceso de AWS). No debes subir este archivo a ningún repositorio público ni compartirlo. Asegúrate de agregar .env a tu archivo .gitignore para evitar su inclusión accidental en sistemas de control de versiones como Git.

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
your_bucket_name/
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

### 7. Realizar transformaciones en Glue
Más adelante, se deben tomar los archivos CSV subidos en la carpeta `raw/`, hacer transformaciones básicas sobre ellos, y almacenarlos en una zona procesada usando Glue. Para esto, abre
[AWS Glue](https://aws.amazon.com/glue/) y crea un nuevo ETL job a partir del script editor con el Spark Engine. Acá puedes subir el código `glue_jobs/trasform_data_glue.py` o copiarlo 
directamente en el editor de código. Adicionalmente, en la configuración de Job details agrega:
- Name: `transform_data_glue`
- IAM Role: `glue_role`
- Job parameters:
  - `--BUCKET_NAME`: `your_bucket_name`
 
Guarda con el botón `Save` y después córrelo con el botón `Run`. El script realiza las siguientes transformaciones a los datos:
1. Estandarizar tipo de documento: el tipo de documento se guarda con todas las letras mayúsculas, como "CC" o "NIT".
2. Estandarizar identificación: se eliminan los caracteres de '-' al número de identificación, un carácter  generalmente presente en las identificaciones tipo NIT.
3. Estandarizar tipo de energía y tipo de transacción: el tipo de energía se guarda con todos sus caracteres en letra minúscula para facilitar las consultas futuras.
4. Estandarizar cantidad comprada y precio: se garantiza que la cantidad comprada y el precio estén almacenados como float.

Cuando la ejecución de la tarea termina, el código guarda la información procesada en formato parquet automáticamente en la capa `staged` que sigue la siguiente estructura:
``` bash
your_bucket_name/
 └── staged/ # Archivos procesados
   ├── clientes/
   │ └── load_date=YYYY-MM-DD/
   │   └── clientes.parquet
   ├── proveedores/
   │ └── load_date=YYYY-MM-DD/
   │   └── proveedores.parquet
   └── transacciones/
     └── load_date=YYYY-MM-DD/
       └── transacciones.parquet
```

 ### 8. Ejecutar detección y Catalogación Automática en Glue
Luego, utilizando AWS Glue se crea un proceso que detecta y cataloga automáticamente los esquemas de los datos almacenados en el datalake. Para esto, crea un nuevo job en AWS Glue a 
partir del script engine y utiliza el código en la ruta `glue_jobs/catalog_data_glue.py`. En la configuración agrega los siguientes componentes:
- Name: `catalog_data_glue`
- IAM Role: `glue_role`
- Job parameters:
  - `--BUCKET_NAME`: `your_bucket_name`
  - `--DATABASE_NAME`: `your_database_name` (nombre de la base de datos deseada)
  - `--IAM_ROLE`: `glue_role`

 Guarda y ejecuta la tarea. Esta tarea se encarga de crear y ejecutar un crawler para detectar y catalogar los datos, registrando las tablas resultantes en una base de datos para que 
 puedan ser consultados fácilmente con queries de SQL en Amazon Athena en el futuro. En adición, debido a que los archivos están organizados por fecha de carga (`load_date`), el Crawler 
 se encarga de crear una nueva columna con este nombre para tener trazabilidad de esta información.

### 9. Consultar información con Athena
Debido a que la información ya está almacenada en la base de datos, es posible realizar consultas en Python fácilmente. En el script  `scripts/athena_queries.py` se utiliza 
[Amazon Athena](https://aws.amazon.com/athena/) para hacer las siguientes consultas:
- Obtener los clientes con tipo de identificación CC.
- Consultar las transacciones y agregar columna de precio total pagado.
- Seleccionar las transacciones que fueron ventas y agruparlas con la información personal de los clientes.

El script imprime en la terminal los resultados de las consultas y adicionalmente guarda en una nueva capa del datalake (carpeta `athena/`) los resultados de las consultas en formato CSV 
por si quieren ser consultados en el futuro.

## Próximos pasos
Luego de tener construido el pipeline con el cual se van a leer y procesar los datos en el datalake se debe crear a infraestructura como código para poder desplegar esta solución en AWS.
La IaC tiene varios beneficios clave, como lo es tener entornos configurados de manera consistente, reproducir la infraestructura en diferentes ambientes fácilmente, y automatizar el despliegue
de la infraestructura más rápido. Para el presente trabajo se consideraría usar **Terraform** como herramienta para lograr esto, ya que es versátil (provedor agnóstico) y funciona con un 
lenguaje declarativo que permite una configuración sencilla. Por otra parte, se configura AWS Lake Formation para centralizar el gobierno, la seguridad y compartir los datos alojados en el
datalake creado.

En la carpeta `iac/` se presenta un estructura tentativa de cómo se podría desarrollar este proceso utilizando Terraform, la cual contiene los siguientes componentes:
- `variables.tf`: definición de las variables que se usarán en main.tf
- `terraform.tfvars`: archivo con los valores para las variables (como el nombre del bucket, base de datos, región, etc.).
- `iam_roles.tf`: definición de los roles y permisos IAM necesarios para interactuar con Glue, Lake Formation, Athena y S3.
- `main.tf`: definición de recursos de infraestructura (como S3, Glue, Lake Formation, Athena, etc.). En este archivo se siguen los siguientes pasos:
  - Configurar proveedor de AWS: se define la región donde se desplegarán los recursos.
  - Se configura el proveedor de AWS con la región donde se desplegarán los recursos.
  - Se crea un bucket de S3 con el nombre definido en la variable `bucket_name`.
  - Se bloqua el acceso público al bucker por seguridad de la información-
  - Se crea la base de datos en el catálogo de Glue.
  - Se vincula la base de datos de Glue con Lake Formation para centralizar el gobierno, la seguridad y compartir los datos almacenados en el datalake.
  - Se configura el trabajo de Glue para procesar y transformar los datos con el script de Python.
  - Se configuran con permisos de Lake Formation para tener permisos de escritura y lectura en la base de datos para el rol de Glue.
  - Se asignan permisos de lectura a los datos almacenados en el bucket de S3 en la carpeta `staged/`.
  - Se define un grupo de trabajo de Athena para ejecutar consultas SQL y almacenar resultados en S3.

De esta forma, después de que se realice una revisión sobre la IaC creada, se podría desplegar esta herramienta en AWS utilizando Terraform con los siguientes comandos:
``` bash
terraform init
terraform plan
terraform apply
```


## Referencias
- [Documentación de AWS](https://docs.aws.amazon.com/)
- [Documentación de Terraform](https://developer.hashicorp.com/terraform/docs)
