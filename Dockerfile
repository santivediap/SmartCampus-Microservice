# Usar una imagen oficial de Python ligera como base
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Evitar que Python escriba archivos .pyc que se generan de forma automática en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Asegurar que la salida de Python se envíe directamente a la terminal
ENV PYTHONUNBUFFERED=1

# Instalamos uv en el contenedor para gestionar las dependencias:
RUN pip install uv

# Copiamos la configuracion de dependencias de los siguientes archivos.
COPY pyproject.toml uv.lock .

# Instalamos y sincronizamos las dependencias (crea el .venv automaticamente).
RUN uv sync

# Añade el entorno virtual al PATH para que el contenedor use sus binarios por defecto
ENV PATH="/app/.venv/bin:$PATH"

# Copiar el resto del código de la aplicación al contenedor
COPY . .

# Puerto en el que se ejecuta Flask (por defecto 5000)
EXPOSE 5000

# Comando para ejecutar la aplicación 
CMD ["uv", "run", "--", "flask", "run", "--host=0.0.0.0"]