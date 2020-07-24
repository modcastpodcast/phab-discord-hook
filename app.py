from datetime import datetime
from os import environ

from flask import Flask, request
import httpx

app = Flask(__name__)

WEBHOOK_URL = environ.get("WEBHOOK_URL")
API_TOKEN = environ.get("API_TOKEN")
API_BASE = environ.get("API_BASE")


def handle_task(data):
    task_transactions = httpx.post(f"{API_BASE}/transaction.search", json={
        "api.token": API_TOKEN,
        "objectIdentifier": data["object"]["phid"]
    }).json()

    httpx.post(WEBHOOK_URL, json={
      "content": str(task_transactions)
    })

    new_transactions = [t["phid"] for t in task_transactions["data"] if t["type"] == "create"]
    hook_transactions = [t["phid"] for t in data["transactions"]]

    task_data = httpx.post(f"{API_BASE}/maniphest.query", json={
        "api.token": API_TOKEN,
        "phids": [
            data["object"]["phid"]
        ]
    }).json()["result"][data["object"]["phid"]]

    author_data = httpx.post(f"{API_BASE}/user.query", json={
        "api.token": API_TOKEN,
        "phids": [
            task_data["authorPHID"]
        ]
    }).json()["result"]["0"]

    if any([new_transaction in hook_transactions for new_transaction in new_transactions]):
        httpx.post(WEBHOOK_URL, json={
          "embeds": [
            {
              "title": task_data["title"],
              "color": 14351509,
              "url": task_data["uri"],
              "author": {
                "name": author_data["realName"],
                "url": author_data["uri"],
                "icon_url": author_data["image"]
              },
              "timestamp": datetime.utcnow().isoformat(),
              "description": f"Task {task_data['objectName']} opened with priority {task_data['priority']}"
            }
          ]
        })

@app.route("/", methods=["POST"])
def hello():
    data = request.get_json()
    if data.get("object", {}).get("type") == "TASK":
        handle_task(data)

    return "okay"


if __name__ == "__main__":
    app.run(host='0.0.0.0')
