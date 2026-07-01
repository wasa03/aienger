"""Google Meet REST API v2 で会議スペースを作成し、参加リンクを表示するスクリプト。

前提:
  1. Google Cloud Console でプロジェクトを作り、Google Meet API を有効化する。
     https://console.cloud.google.com/apis/library/meet.googleapis.com
  2. 「OAuth 同意画面」を設定し、「認証情報 → OAuth クライアント ID (デスクトップ アプリ)」を作成、
     JSON をダウンロードして本スクリプトと同じディレクトリに `credentials.json` として保存する。
  3. 必要なライブラリをインストール:
       pip install google-auth google-auth-oauthlib google-api-python-client

初回実行時にブラウザが開き、Google アカウントで認可すると `token.json` が保存され、以降は再利用される。
"""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/meetings.space.created"]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR.parent / "_json" / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_credentials() -> Credentials:
    """OAuth 認可を行い、資格情報を返す。既存トークンがあれば再利用/更新する。"""
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


def create_meeting_space(access_type: str = "TRUSTED") -> dict:
    """Meet の会議スペースを作成し、レスポンス dict を返す。

    access_type:
      - "OPEN"    : 誰でも参加可
      - "TRUSTED" : 招待済み・同一組織のユーザーが参加可 (デフォルト)
      - "RESTRICTED": 招待されたユーザーのみ参加可
    """
    creds = get_credentials()
    service = build("meet", "v2", credentials=creds)

    body = {"config": {"access_type": access_type}}
    space = service.spaces().create(body=body).execute()
    return space


def main() -> None:
    space = create_meeting_space(access_type="TRUSTED")
    print("=== Google Meet 会議スペースを作成しました ===")
    print(f"参加リンク : {space.get('meetingUri')}")
    print(f"会議コード : {space.get('meetingCode')}")
    print(f"スペース名 : {space.get('name')}")


if __name__ == "__main__":
    main()
