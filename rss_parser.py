import feedparser
import requests
import sys
import os
import json
import time
from bs4 import BeautifulSoup

def send_request_with_retry(webhook_url, data, retries=5, wait=60):
    for attempt in range(retries):
        response = requests.post(webhook_url, json=data)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", wait))
            print(f"Rate limit exceeded. Retrying in {retry_after} seconds...")
            time.sleep(retry_after)
        else:
            response.raise_for_status()
            return
    raise Exception("Failed to send request after several retries")

def fetch_and_send_rss(rss_url, webhook_url, state_file):
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        print("No new entries found in the RSS feed.")
        return

    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            last_entries = json.load(f)
    else:
        last_entries = []

    new_entries = [entry for entry in feed.entries if entry.id not in last_entries]

    if not new_entries:
        print("No new entries to process.")
        return

    for entry in new_entries:
        title = entry.get("title", "No title")
        link = entry.get("link", "No link")
        summary = entry.get("summary", "No description")
        category = entry.get("category", "トピックス").lower()

        info = {
            "メンテナンス": {
                "icon_url": "https://lds-img.finalfantasyxiv.com/h/U/6qzbI-6AwlXAfGhCBZU10jsoLA.png",
                "color": 13413161,
            },
            "お知らせ": {
                "icon_url": "https://lds-img.finalfantasyxiv.com/h/M/hu9OeFAv1VWVEJiaj9VWutGZDY.png",
                "color": 13421772,
            },
            "障害情報": {
                "icon_url": "https://lds-img.finalfantasyxiv.com/h/4/8PRdUkaKFa8R5BKeQjRyItGoxY.png",
                "color": 10042685,
            },
            "アップデート": {
                "icon_url": "https://lds-img.finalfantasyxiv.com/h/a/dFnS0OBVXIsmB74L65R7VHlpd8.png",
                "color": 7051581,
            },
            "トピックス": {
                "icon_url": "https://lds-img.finalfantasyxiv.com/h/W/_v7zlp4yma56rKwd8pIzU8wGFc.png",
                "color": 13404201,
            },
        }

        entry_info = info.get(category, info["トピックス"])

        if category == "トピックス":
            plain_text_summary = BeautifulSoup(summary, "html.parser").get_text()
            data = {
                "embeds": [
                    {
                        "color": entry_info["color"],
                        "title": title,
                        "url": link,
                        "author": {
                            "name": f"{category.capitalize()}",
                            "icon_url": entry_info["icon_url"],
                        },
                        "description": plain_text_summary,
                    }
                ]
            }
        else:
            soup = BeautifulSoup(entry.get("content")[0]["value"], "html.parser")
            image_tag = soup.find("img", class_="mdl-img__visual")
            image_url = image_tag["src"] if image_tag else ""

            data = {
                "embeds": [
                    {
                        "color": entry_info["color"],
                        "title": title,
                        "url": link,
                        "author": {
                            "name": f"{category.capitalize()}",
                            "icon_url": entry_info["icon_url"],
                        },
                        "image": {"url": image_url} if image_url else {},
                    }
                ]
            }

        send_request_with_retry(webhook_url, data)

    latest_ids = [entry.id for entry in feed.entries[:10]]
    with open(state_file, 'w') as f:
        json.dump(latest_ids, f)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rss_parser.py <RSS_URL>")
        sys.exit(1)

    rss_url = sys.argv[1]
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("WEBHOOK_URL environment variable is not set.")
        sys.exit(1)

    state_file = os.path.join(os.path.dirname(__file__), f"{rss_url.split('/')[-2]}_state.json")
    fetch_and_send_rss(rss_url, webhook_url, state_file)
