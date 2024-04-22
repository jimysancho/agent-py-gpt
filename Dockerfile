FROM python:3.11.7-slim-bullseye
WORKDIR /app

ADD . /app

RUN pip install --upgrade pip


RUN apt-get update && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install streamlit httpx
EXPOSE 8501

CMD streamlit run streamlit_app.py