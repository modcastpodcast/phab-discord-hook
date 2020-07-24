FROM python:latest

RUN pip install flask httpx gunicorn

RUN gunicorn --bind 0.0.0.0:5000 app:app
