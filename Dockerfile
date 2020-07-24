FROM python:latest

WORKDIR /app

COPY . .

RUN pip install flask httpx gunicorn

CMD gunicorn --bind 0.0.0.0:5000 app:app
