"""
Zoom API (Server-to-Server OAuth) を使って会議を作成し、
会議ID・パスワード・会議リンクを表示するスクリプト。

事前準備:
  1. https://marketplace.zoom.us/ で「Server-to-Server OAuth」アプリを作成
  2. Scopes に「meeting:write:meeting:admin」(または meeting:write:admin) を追加
  3. Account ID / Client ID / Client Secret を .env に設定

  .env の例:
    ZOOM_ACCOUNT_ID=xxxxxxxx
    ZOOM_CLIENT_ID=xxxxxxxx
    ZOOM_CLIENT_SECRET=xxxxxxxx

実行:
  pip install requests python-dotenv
  python create_zoom_meeting.py --topic "定例会議" --start "2026-12-01 10:00" --duration 60
"""

import argparse
import os
import secrets
import string
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

TOKEN_URL = "https://zoom.us/oauth/token"
API_BASE = "https://api.zoom.us/v2"


def get_access_token(account_id: str, client_id: str, client_secret: str) -> str:
    """Server-to-Server OAuth でアクセストークンを取得する。"""
    resp = requests.post(
        TOKEN_URL,
        params={"grant_type": "account_credentials", "account_id": account_id},
        auth=(client_id, client_secret),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def generate_password(length: int = 8) -> str:
    """Zoom の会議パスコード用ランダム文字列を生成する(英数字, 最大10文字)。"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_meeting(
    token: str,
    topic: str,
    start_time: datetime | None,
    duration: int,
    timezone: str = "Asia/Tokyo",
    password: str | None = None,
    user_id: str = "me",
) -> dict:
    """会議を作成し、Zoom API のレスポンス(dict)を返す。"""
    payload = {
        "topic": topic,
        "type": 2 if start_time else 1,  # 2: 予約会議, 1: インスタント会議
        "duration": duration,
        "timezone": timezone,
        "password": password or generate_password(),
        "settings": {
            "join_before_host": False,
            "waiting_room": True,
            "mute_upon_entry": True,
        },
    }
    if start_time:
        # timezone を指定する場合、末尾に Z を付けないローカル時刻で渡す
        payload["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%S")

    resp = requests.post(
        f"{API_BASE}/users/{user_id}/meetings",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30,
    )
    if resp.status_code != 201:
        raise RuntimeError(f"会議作成に失敗しました ({resp.status_code}): {resp.text}")
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Zoom 会議を作成する")
    parser.add_argument("--topic", default="ミーティング", help="会議名")
    parser.add_argument("--start", help='開始日時 "YYYY-MM-DD HH:MM" (省略時はインスタント会議)')
    parser.add_argument("--duration", type=int, default=60, help="会議時間(分)")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="タイムゾーン")
    parser.add_argument("--password", help="パスコード(省略時は自動生成)")
    args = parser.parse_args()

    load_dotenv()
    account_id = os.getenv("ZOOM_ACCOUNT_ID")
    client_id = os.getenv("ZOOM_CLIENT_ID")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET")
    if not all([account_id, client_id, client_secret]):
        sys.exit("ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET を環境変数または .env に設定してください。")

    start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M") if args.start else None

    token = get_access_token(account_id, client_id, client_secret)
    meeting = create_meeting(
        token,
        topic=args.topic,
        start_time=start_time,
        duration=args.duration,
        timezone=args.timezone,
        password=args.password,
    )

    print("=== Zoom 会議を作成しました ===")
    print(f"会議名     : {meeting['topic']}")
    if meeting.get("start_time"):
        start_utc = datetime.fromisoformat(meeting["start_time"].replace("Z", "+00:00"))
        start_local = start_utc.astimezone(ZoneInfo(args.timezone))
        print(f"開始日時   : {start_local:%Y-%m-%d %H:%M} ({args.timezone})")
    else:
        print("開始日時   : (インスタント会議・Zoomの予定一覧には表示されません)")
    print(f"会議ID     : {meeting['id']}")
    print(f"パスワード : {meeting.get('password', '')}")
    print(f"参加リンク : {meeting['join_url']}")
    print(f"ホスト用   : {meeting['start_url'][:60]}...  (ホスト専用・共有しないでください)")


if __name__ == "__main__":
    main()
