"""Google Calendar API 経由で Meet 付きイベントを作成するスクリプト。

Meet REST API と違い、開始/終了時刻・タイトル・出席者を指定できる。
Google カレンダー上にも予定として登録され、招待メールも送信できる。

前提:
  1. Google Cloud Console で Calendar API を有効化する。
     https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
  2. OAuth クライアント ID (デスクトップ アプリ) の JSON を `credentials.json` として保存。
  3. pip install google-auth google-auth-oauthlib google-api-python-client
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token_calendar.json"

JST = timezone(timedelta(hours=9))


def get_credentials() -> Credentials:
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"OAuth クライアント ID の JSON が見つかりません: {CREDENTIALS_FILE}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def create_meet_event(
    summary: str,
    start: datetime,
    duration_minutes: int = 60,
    attendees: list[str] | None = None,
    description: str = "",
) -> dict:
    """Meet リンク付きの Google カレンダーイベントを作成する。"""
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    end = start + timedelta(minutes=duration_minutes)
    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Tokyo"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Tokyo"},
        "attendees": [{"email": e} for e in (attendees or [])],
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",
        )
        .execute()
    )
    return event


def main() -> None:
    start = datetime.now(JST) + timedelta(hours=1)
    event = create_meet_event(
        summary="サンプルミーティング",
        start=start,
        duration_minutes=30,
        attendees=[],
        description="Python スクリプトから作成したテスト会議",
    )

    meet_link = event.get("hangoutLink")
    print("=== カレンダーイベントを作成しました ===")
    print(f"タイトル   : {event.get('summary')}")
    print(f"開始       : {event['start']['dateTime']}")
    print(f"Meet リンク: {meet_link}")
    print(f"イベント URL: {event.get('htmlLink')}")


if __name__ == "__main__":
    main()
