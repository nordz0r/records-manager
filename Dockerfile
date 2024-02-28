# Использование базового образа
FROM python:3.9.0-alpine

# Установка рабочей директории в контейнере
WORKDIR /app

# Копирование файлов Python
COPY app/main.py requirements.txt ./

# Копирование директорий static и templates целиком
COPY app/static ./static
COPY app/templates ./templates

# Установка build зависимостей, установка зависимостей из pip и удаление build зависимостей
RUN apk add --no-cache --virtual .build-deps build-base \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Команда для запуска приложения
CMD ["python","-u", "main.py"]
