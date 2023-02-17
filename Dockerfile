FROM python:3.9.0-alpine

WORKDIR /app

COPY requirements.txt app/main.py /app
COPY app/static static
COPY app/templates templates

RUN apk add --no-cache build-base && pip install -r requirements.txt

CMD ["python","-u", "main.py"]