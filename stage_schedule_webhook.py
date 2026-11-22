import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


JST = timezone(timedelta(hours=9))
ROTATION_MINUTES = 60
STATE_FILE = Path("stage_schedule_state.json")
WEBHOOK_URL_ENV = "DISCORD_STAGE_WEBHOOK_URL"
STAGE_ZERO_TIME_ENV = "STAGE_ZERO_TIME"
DEFAULT_STAGE_ZERO_TIME = "2026-05-03T00:00:00+09:00"
PAYLOAD_VERSION = 3

STAGES = [
    "パライストラ",
    "ヴォルカニック・ハート",
    "ベイサイド・バトルグラウンド",
    "クラウドナイン",
    "東方絡繰御殿",
    "ハルモニア戦争図書館",
    "レッド・サンズ",
]

STAGE_COLORS = {
    "パライストラ": 0xD4CC99,
    "ヴォルカニック・ハート": 0xCC5533,
    "ベイサイド・バトルグラウンド": 0x2D8FCB,
    "クラウドナイン": 0x75B9E7,
    "東方絡繰御殿": 0xB6742F,
    "ハルモニア戦争図書館": 0x8367C7,
    "レッド・サンズ": 0xB84535,
}


def parse_stage_zero_time():
    value = os.getenv(STAGE_ZERO_TIME_ENV) or DEFAULT_STAGE_ZERO_TIME

    stage_zero_time = datetime.fromisoformat(value)
    if stage_zero_time.tzinfo is None:
        stage_zero_time = stage_zero_time.replace(tzinfo=JST)

    return stage_zero_time.astimezone(JST)


def get_current_stage(now, stage_zero_time):
    elapsed_minutes = int((now - stage_zero_time).total_seconds() // 60)
    rotation_count = elapsed_minutes // ROTATION_MINUTES
    index = rotation_count % len(STAGES)
    next_index = (index + 1) % len(STAGES)
    next_change = stage_zero_time + timedelta(
        minutes=(rotation_count + 1) * ROTATION_MINUTES
    )

    return STAGES[index], STAGES[next_index], next_change


def load_state():
    if not STATE_FILE.exists():
        return {}

    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )


def build_weekly_table(stage_zero_time):
    # The seven hourly slots repeat exactly 24 times per week.
    monday = stage_zero_time.replace(hour=0) - timedelta(days=stage_zero_time.weekday())
    rows = ["開始時        月 火 水 木 金 土 日"]
    for hour in range(len(STAGES)):
        hours = " ".join(f"{h:02d}" for h in range(hour, 24, len(STAGES)))
        numbers = []
        for day in range(7):
            start = monday + timedelta(days=day, hours=hour)
            stage, _, _ = get_current_stage(start, stage_zero_time)
            numbers.append(str(STAGES.index(stage) + 1))
        rows.append(f"{hours:<11}   " + "  ".join(numbers))

    return "```\n" + "\n".join(rows) + "\n```"


def build_stage_payload(current_stage, next_change, stage_zero_time):
    slot = timedelta(minutes=ROTATION_MINUTES)
    start = next_change - slot
    first_index = STAGES.index(current_stage)
    lines = []
    for offset in range(len(STAGES)):
        index = (first_index + offset) % len(STAGES)
        when = start + offset * slot
        lines.append(f"<t:{int(when.timestamp())}:f>　`{index + 1}` {STAGES[index]}")

    minute = f"{stage_zero_time.minute:02d}分"
    if stage_zero_time.second or stage_zero_time.microsecond:
        seconds = stage_zero_time.time().isoformat().split(":")[-1]
        minute += f"{seconds}秒"
    return {
        "content": "",
        "embeds": [
            {
                "title": "PvP ステージスケジュール",
                "description": f"クリスタルコンフリクトの各ステージは開始から{ROTATION_MINUTES}分間です。",
                "color": STAGE_COLORS.get(current_stage, 0xD4CC99),
                "fields": [
                    {
                        "name": "ステージの開始時刻",
                        "value": "\n".join(lines),
                        "inline": False,
                    },
                    {
                        "name": f"週間時刻表（日本時間・毎時{minute}開始）",
                        "value": "開始時刻の行と曜日の列が交わる番号が、その時間のステージです。\n"
                        + build_weekly_table(stage_zero_time),
                        "inline": False,
                    },
                ],
            }
        ],
        "allowed_mentions": {"parse": []},
    }


def post_new_message(webhook_url, payload):
    response = requests.post(f"{webhook_url}?wait=true", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["id"]


def edit_message(webhook_url, message_id, payload):
    response = requests.patch(
        f"{webhook_url}/messages/{message_id}",
        json=payload,
        timeout=10,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return message_id


def main():
    webhook_url = os.getenv(WEBHOOK_URL_ENV)
    if not webhook_url:
        print(f"{WEBHOOK_URL_ENV} is not set. Skipping stage schedule update.")
        return

    stage_zero_time = parse_stage_zero_time()
    current_stage, next_stage, next_change = get_current_stage(
        datetime.now(JST), stage_zero_time
    )
    rotation_key = next_change.strftime("%Y-%m-%dT%H:%M:%S%z")
    state = load_state()

    if (
        state.get("message_id")
        and state.get("last_rotation_key") == rotation_key
        and state.get("payload_version") == PAYLOAD_VERSION
    ):
        print("Stage schedule message is already current.")
        return

    payload = build_stage_payload(current_stage, next_change, stage_zero_time)
    message_id = state.get("message_id")

    if message_id:
        message_id = edit_message(webhook_url, message_id, payload)

    if not message_id:
        message_id = post_new_message(webhook_url, payload)

    save_state(
        {
            "message_id": message_id,
            "last_rotation_key": rotation_key,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "payload_version": PAYLOAD_VERSION,
            "updated_at": datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
    )
    print(f"Updated stage schedule message for {current_stage}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(error, file=sys.stderr)
        sys.exit(1)
