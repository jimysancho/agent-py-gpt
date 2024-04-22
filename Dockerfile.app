FROM python:3.11.7-slim-bullseye
WORKDIR /app

ADD . /app

RUN pip install --upgrade pip


RUN apt-get update && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install "uvicorn[standard]" 


EXPOSE 3000

CMD uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload --log-level debug