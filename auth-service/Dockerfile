FROM python:3.11-slim

RUN apt-get update && apt-get install -y netcat-openbsd

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt --timeout=1000 --retries=10

COPY . .

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

CMD ["/wait-for-db.sh", "auth_db", "5432", "python", "manage.py", "runserver", "0.0.0.0:8000"]
