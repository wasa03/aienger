"""
Google Calendar API 経由で Google Meet 付きの予定を作成する。
(4-3-2_3/create_meet_via_calendar.py をもとに、ローカルサイトから使えるようにしたもの)

前提:
  - Google Cloud Console で Calendar API を有効化
  - OAuth クライアント ID (デスクトップ アプリ) の JSON を ../_json/credentials.json に置く
  - 初回はブラウザが開くので Google アカウントで許可する → token_calendar.json に保存され、以降は自動

単体でも実行可能(初回ログインだけ済ませたいとき):
  .venv/bin/python create_meet.py --login
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR.parent / "_json" / "credentials.json"
TOKEN_FILE = BASE_DIR / "token_calendar.json"


def get_credentials() -> Credentials:
    """保存済みのログイン情報を使う。無ければブラウザでGoogleログインする。"""
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(f"OAuth クライアント ID の JSON が見つかりません: {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def create_meet_event(summary: str, start: datetime, duration_minutes: int = 60) -> dict:
    """Meet リンク付きの Google カレンダー予定を作成し、結果をまとめた dict を返す。

    start はタイムゾーンなしの日本時間として扱う。招待メールは送らない。
    """
    service = build("calendar", "v3", credentials=get_credentials(), cache_discovery=False)

    end = start + timedelta(minutes=duration_minutes)
    body = {
        "summary": summary,
        "start": {"dateTime": start.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Asia/Tokyo"},
        "end": {"dateTime": end.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Asia/Tokyo"},
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
    event = (
        service.events()
        .insert(calendarId="primary", body=body, conferenceDataVersion=1, sendUpdates="none")
        .execute()
    )

    conf = event.get("conferenceData", {})
    return {
        "summary": event.get("summary", summary),
        "meet_url": event.get("hangoutLink", ""),
        "meeting_code": conf.get("conferenceId", ""),
        "event_url": event.get("htmlLink", ""),
        "status": conf.get("createRequest", {}).get("status", {}).get("statusCode", ""),
    }


if __name__ == "__main__":
    if "--login" in sys.argv:
        get_credentials()
        print("Googleへのログインが完了しました。")
    else:
        r = create_meet_event("テスト会議", datetime.now() + timedelta(hours=1), 30)
        print(r)
