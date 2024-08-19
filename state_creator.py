import feedparser
import json
import sys
import os


def save_latest_entries(rss_url, state_file):
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        print("No entries found in the RSS feed.")
        return

    # 最新のエントリーIDを抽出
    latest_ids = [entry.id for entry in feed.entries]

    # エントリーIDをJSONファイルに保存
    with open(state_file, "w") as f:
        json.dump(latest_ids, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(latest_ids)} entries to {state_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python state_creator.py <RSS_URL>")
        sys.exit(1)

    rss_url = sys.argv[1]
    file_name = os.path.splitext(os.path.basename(rss_url))[
        0
    ]  # ファイル名部分を取得して拡張子を除去
    state_file = os.path.join(os.path.dirname(__file__), f"{file_name}_state.json")
    save_latest_entries(rss_url, state_file)
