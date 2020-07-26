from datetime import datetime
from os import environ

from flask import Flask, request
import httpx

app = Flask(__name__)

PHABRICATOR_WEBHOOK_URL = environ.get("PHABRICATOR_WEBHOOK_URL")
GHOST_WEBHOOK_URL = environ.get("GHOST_WEBHOOK_URL")

API_TOKEN = environ.get("API_TOKEN")
API_BASE = environ.get("API_BASE")


def handle_task(data):
    task_transactions = httpx.post(f"{API_BASE}/transaction.search", data={
        "api.token": API_TOKEN,
        "objectIdentifier": data["object"]["phid"]
    })

    task_transactions = task_transactions.json()["result"]

    new_transactions = [t["phid"] for t in task_transactions["data"] if t["type"] == "create"]
    hook_transactions = [t["phid"] for t in data["transactions"]]

    task_data = httpx.post(f"{API_BASE}/maniphest.query", data={
        "api.token": API_TOKEN,
        "phids[0]": data["object"]["phid"]
    }).json()["result"][data["object"]["phid"]]

    author_data = httpx.post(f"{API_BASE}/user.query", data={
        "api.token": API_TOKEN,
        "phids[0]": task_data["authorPHID"]
    }).json()["result"][0]

    form_data = {}

    for i, project_phid in enumerate(task_data["projectPHIDs"]):
        form_data[f"phids[{i}]"] = project_phid

    form_data["api.token"] = API_TOKEN

    project_data = httpx.post(
        f"{API_BASE}/project.query",
        data=form_data
    ).json()["result"]["data"]

    projects = [p["name"] for p in project_data.values()]

    project_str = "**›› Projects**\n"

    for project in projects:
        project_str += f"• {project}\n"

    if any(
        [new_transaction in hook_transactions for new_transaction in new_transactions]
    ):
        httpx.post(PHABRICATOR_WEBHOOK_URL, json={
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
              "description": f"**›› Task ID**\n{task_data['objectName']}\n\n**›› Priority**\n{task_data['priority']}\n\n{project_str}"
            }
          ]
        })

@app.route("/", methods=["POST"])
def phabricator():
    """
    Handle data ingested from Phabricator.
    """
    data = request.get_json()
    if data.get("object", {}).get("type") == "TASK":
        handle_task(data)

    return "okay"

@app.route("/ghost/publish", methods=["POST"])
def ghost():
    """
    Handle publish data ingested from Ghost.
    """
    data = request.get_json()["post"]["current"]

    url = data['url']

    url += "?utm_medium=discord&utm_source=announcement"
    url += f"&utm_campaign={data['slug']}"

    webhook_data = {
      "embeds": [
        {
          "title": f":mega: {data['title']}",
          "description": data['custom_excerpt'],
          "url": url,
          "color": 16711790,
          "timestamp": datetime.utcnow().isoformat(),
          "image": {
            "url": data['feature_image']
          },
          "author": {
            "name": data['primary_author']['name'],
            "url": "https://modcast.network/author/" + data['primary_author']['slug'],
            "icon_url": data['primary_author']['profile_image']
          }
        }
      ]
    }

    httpx.post(GHOST_WEBHOOK_URL, json=webhook_data)

    return "okay"

if __name__ == "__main__":
    app.run(host='0.0.0.0')
