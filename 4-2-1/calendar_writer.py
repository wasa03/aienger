"""
Google Calendar にサービスアカウントで予定を追加するサンプル。

前提:
  pip install google-auth google-auth-httplib2 google-api-python-client

サービスアカウントの準備:
  1. Google Cloud Console で Google Calendar API を有効化
  2. サービスアカウントを作成し JSON キーをダウンロード
  3. Google カレンダーの「設定と共有」>「特定のユーザーとの共有」に
     サービスアカウントのメールアドレスを追加（「予定の変更」権限）
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ---- 設定 ----
# サービスアカウントの JSON キーファイル（リポジトリ直下の _json/ に配置。Git 管理外）
SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "_json", "level-racer-495902-u8-c2342607c89b.json"
)
CALENDAR_ID = "f7a07515dd144543d403753617eda5f9f2283014066e25a25d18786505721d88@group.calendar.google.com"                # カレンダー ID（共有カレンダーは xxx@group.calendar.google.com）
TIMEZONE = "Asia/Tokyo"

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def create_event(service, summary: str, start: datetime, end: datetime, description: str = "", location: str = "") -> dict:
    """時間指定の予定を作成して返す。"""
    fmt = "%Y-%m-%dT%H:%M:%S"
    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start.strftime(fmt), "timeZone": TIMEZONE},
        "end":   {"dateTime": end.strftime(fmt),   "timeZone": TIMEZONE},
    }
    return service.events().insert(calendarId=CALENDAR_ID, body=event).execute()


def create_allday_event(service, summary: str, date: datetime, description: str = "") -> dict:
    """終日予定を作成して返す。"""
    event = {
        "summary": summary,
        "description": description,
        "start": {"date": date.strftime("%Y-%m-%d")},
        "end":   {"date": (date + timedelta(days=1)).strftime("%Y-%m-%d")},
    }
    return service.events().insert(calendarId=CALENDAR_ID, body=event).execute()


def prompt_event() -> tuple[str, datetime, datetime]:
    """ユーザーからタイトル・日付・時間を対話的に受け取り (summary, start, end) を返す。"""
    tz = ZoneInfo(TIMEZONE)

    summary = input("タイトル: ").strip()

    while True:
        date_str = input("日付 (例: 2026-05-15): ").strip()
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            break
        except ValueError:
            print("  形式が正しくありません。YYYY-MM-DD で入力してください。")

    while True:
        start_str = input("開始時刻 (例: 10:00): ").strip()
        try:
            st = datetime.strptime(start_str, "%H:%M")
            break
        except ValueError:
            print("  形式が正しくありません。HH:MM で入力してください。")

    while True:
        end_str = input("終了時刻 (例: 11:30): ").strip()
        try:
            et = datetime.strptime(end_str, "%H:%M")
            break
        except ValueError:
            print("  形式が正しくありません。HH:MM で入力してください。")

    start = datetime(date.year, date.month, date.day, st.hour, st.minute, tzinfo=tz)
    end   = datetime(date.year, date.month, date.day, et.hour, et.minute, tzinfo=tz)
    return summary, start, end


def main():
    service = get_service()

    summary, start, end = prompt_event()
    event = create_event(service, summary=summary, start=start, end=end)
    print(f"\n作成しました: {event['summary']} ({start.strftime('%Y-%m-%d %H:%M')} 〜 {end.strftime('%H:%M')})")
    print(f"URL: {event.get('htmlLink')}")


if __name__ == "__main__":
    main()
