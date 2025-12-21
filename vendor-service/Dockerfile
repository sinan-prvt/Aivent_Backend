FROM python:3.11

RUN apt-get update && apt-get install -y netcat-openbsd

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FIX 1 — create keys folder
RUN mkdir -p /app/keys

# FIX 2 — add wait-for-db
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

CMD ["/wait-for-db.sh", "vendor_db", "5432", "python", "manage.py", "runserver", "0.0.0.0:8000"]
