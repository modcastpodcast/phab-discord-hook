from os import environ

from flask import Flask, request
import httpx

app = Flask(__name__)

WEBHOOK_URL = environ.get("WEBHOOK_URL")


@app.route("/", methods=["POST"])
def hello():
    httpx.post(WEBHOOK_URL, json={
        "content": str(request.get_json())
    })
    return "okay"


if __name__ == "__main__":
    app.run(host='0.0.0.0')
