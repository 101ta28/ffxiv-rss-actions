import feedparser
import requests
import sys
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def fetch_and_send_rss(rss_url, webhook_url):
    feed = feedparser.parse(rss_url)
    if feed.entries:
        latest_entry = feed.entries[0]
        title = latest_entry.get("title", "No title")
        link = latest_entry.get("link", "No link")
        summary = latest_entry.get("summary", "No description")
        category = latest_entry.get("category", "トピックス").lower()

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

        if "news" in link:
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
                    }
                ]
            }
        else:
            soup = BeautifulSoup(
                latest_entry.get("content")[0]["value"], "html.parser"
            )
            plain_text_summary = soup.get_text()
            image_tag = soup.find("img", class_="mdl-img__visual")
            image_url = image_tag["src"] if image_tag else ""

            data = {
                "embeds": [
                    {
                        "color": entry_info["color"],
                        "title": title,
                        "url": link,
                        "author": {
                            "name": "トピックス",
                            "icon_url": entry_info["icon_url"],
                        },
                        "description": plain_text_summary,
                        "image": {"url": image_url},
                    }
                ]
            }

        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
    else:
        print("No new entries found in the RSS feed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rss_parser.py <RSS_URL>")
        sys.exit(1)

    rss_url = sys.argv[1]
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("WEBHOOK_URL environment variable is not set.")
        sys.exit(1)

    fetch_and_send_rss(rss_url, webhook_url)
