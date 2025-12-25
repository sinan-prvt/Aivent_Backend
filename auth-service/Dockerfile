FROM python:3.11-slim@sha256:7cd0079a9bd8800c81632d65251048fc2848bf9afda542224b1b10e0cae45575

RUN apt-get update \
 && apt-get install -y --no-install-recommends netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

CMD ["/wait-for-db.sh", "auth_db", "5432", "python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
