"""Zoom API (Server-to-Server OAuth) で会議を作成し、会議 ID・パスワード・参加リンクを表示するスクリプト。

前提:
  1. Zoom App Marketplace (https://marketplace.zoom.us/) で
     「Develop → Build App → Server-to-Server OAuth」アプリを作成する。
  2. Scopes に会議作成の権限を追加する。
       - meeting:write:meeting (または旧形式の meeting:write:admin)
  3. アプリを Activate し、App Credentials の
     Account ID / Client ID / Client Secret を控える。
  4. 認証情報を以下のいずれかで渡す。
     (a) 環境変数
           ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET
     (b) リポジトリ直下の `_json/zoom_credentials.json` (.gitignore 済み)
           {
             "account_id": "xxxx",
             "client_id": "xxxx",
             "client_secret": "xxxx"
           }
  5. 必要なライブラリをインストール:
       pip install requests

実行例:
  python create_zoom_meeting.py
  python create_zoom_meeting.py --topic "定例ミーティング" --start "2026-12-01 10:00" --duration 30
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR.parent / "_json" / "zoom_credentials.json"

TOKEN_URL = "https://zoom.us/oauth/token"
API_BASE_URL = "https://api.zoom.us/v2"
TIMEZONE = "Asia/Tokyo"


def load_credentials() -> dict[str, str]:
    """環境変数 → JSON ファイルの順で Zoom の認証情報を読み込む。"""
    creds = {
        "account_id": os.environ.get("ZOOM_ACCOUNT_ID"),
        "client_id": os.environ.get("ZOOM_CLIENT_ID"),
        "client_secret": os.environ.get("ZOOM_CLIENT_SECRET"),
    }
    if all(creds.values()):
        return creds  # type: ignore[return-value]

    if CREDENTIALS_FILE.exists():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        for key in creds:
            creds[key] = creds[key] or data.get(key)

    missing = [k for k, v in creds.items() if not v]
    if missing:
        raise RuntimeError(
            "Zoom の認証情報が不足しています: "
            + ", ".join(missing)
            + f"\n環境変数 ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET か "
            f"{CREDENTIALS_FILE} を設定してください。"
        )
    return creds  # type: ignore[return-value]


def get_access_token(creds: dict[str, str]) -> str:
    """Server-to-Server OAuth でアクセストークン (有効期限 1 時間) を取得する。"""
    resp = requests.post(
        TOKEN_URL,
        params={"grant_type": "account_credentials", "account_id": creds["account_id"]},
        auth=(creds["client_id"], creds["client_secret"]),
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"アクセストークンの取得に失敗しました ({resp.status_code}): {resp.text}")
    return resp.json()["access_token"]


def generate_password(length: int = 10) -> str:
    """Zoom の会議パスコード (最大 10 文字、英数字) をランダム生成する。"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_meeting(
    access_token: str,
    topic: str,
    start_time: datetime,
    duration: int,
    password: str,
    user_id: str = "me",
) -> dict:
    """予約会議 (type=2) を作成し、レスポンス dict を返す。"""
    body = {
        "topic": topic,
        "type": 2,  # 2 = 予約会議 (scheduled meeting)
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": duration,
        "timezone": TIMEZONE,
        "password": password,
        "settings": {
            "join_before_host": False,
            "waiting_room": True,
            "mute_upon_entry": True,
            "host_video": True,
            "participant_video": False,
        },
    }
    resp = requests.post(
        f"{API_BASE_URL}/users/{user_id}/meetings",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )
    if resp.status_code != 201:
        raise RuntimeError(f"会議の作成に失敗しました ({resp.status_code}): {resp.text}")
    return resp.json()


def format_meeting_id(meeting_id: int | str) -> str:
    """会議 ID を Zoom 表記 (例: 123 4567 8901) に整形する。"""
    s = str(meeting_id)
    if len(s) == 11:
        return f"{s[:3]} {s[3:7]} {s[7:]}"
    if len(s) == 10:
        return f"{s[:3]} {s[3:6]} {s[6:]}"
    return s


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zoom 会議を作成します。")
    parser.add_argument("--topic", default="Zoom ミーティング", help="会議名")
    parser.add_argument(
        "--start",
        help='開始日時 (例: "2026-12-01 10:00", Asia/Tokyo)。省略時は 1 時間後',
    )
    parser.add_argument("--duration", type=int, default=60, help="会議時間 (分)")
    parser.add_argument("--password", help="パスコード (省略時はランダム生成, 最大 10 文字)")
    parser.add_argument("--user", default="me", help="ホストのユーザー ID またはメール (既定: me)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    tz = ZoneInfo(TIMEZONE)
    if args.start:
        start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    else:
        start_time = (datetime.now(tz) + timedelta(hours=1)).replace(second=0, microsecond=0)

    password = args.password or generate_password()
    if len(password) > 10:
        raise ValueError("パスコードは 10 文字以内で指定してください。")

    creds = load_credentials()
    token = get_access_token(creds)
    meeting = create_meeting(
        token,
        topic=args.topic,
        start_time=start_time,
        duration=args.duration,
        password=password,
        user_id=args.user,
    )

    print("=== Zoom 会議を作成しました ===")
    print(f"会議名       : {meeting.get('topic')}")
    print(f"開始日時     : {start_time.strftime('%Y-%m-%d %H:%M')} ({TIMEZONE})")
    print(f"時間         : {meeting.get('duration')} 分")
    print(f"ミーティングID: {format_meeting_id(meeting.get('id'))}")
    print(f"パスコード   : {meeting.get('password')}")
    print(f"参加リンク   : {meeting.get('join_url')}")
    print(f"ホスト用リンク: {meeting.get('start_url')}")


if __name__ == "__main__":
    main()
