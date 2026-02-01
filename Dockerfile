# Base image
FROM python:3.9-slim

# Çevresel değişkenler
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Sistem bağımlılıkları (OSMnx ve diğer bilimsel kütüphaneler için)
RUN apt-get update && apt-get install -y \
    build-essential \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kaynak kodunu kopyala
COPY src/ src/

# Portu belirt (belgesel amaçlı)
EXPOSE 8000

# Varsayılan komut (API için)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
