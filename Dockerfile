# Dockerfile para despliegue en Fly.io
# Esta única imagen será usada tanto para la API web como para el worker.
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY src/ /app/src/

# El comando para iniciar la aplicación (CMD) se especificará en el archivo fly.toml
# Esto nos permite usar la misma imagen para diferentes procesos (web y worker).
