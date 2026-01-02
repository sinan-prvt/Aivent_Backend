FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
