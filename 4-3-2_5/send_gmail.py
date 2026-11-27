"""Gmail API を使って指定した宛先にメールを送信するスクリプト。

前提:
  1. 送信元にする Google アカウントで Google Cloud プロジェクトを作り、Gmail API を有効化する。
     https://console.cloud.google.com/apis/library/gmail.googleapis.com
  2. そのプロジェクトの OAuth クライアント ID (デスクトップ アプリ) の JSON を
     ../_json/credentials_gmail.json に置く (4-3-2_4 の credentials.json とは別ファイル)。
  3. pip install -r requirements.txt

使い方:
  python send_gmail.py --to someone@example.com --subject "件名" --body "本文"
  python send_gmail.py --to a@example.com b@example.com --cc c@example.com \
      --subject "資料送付" --body-file body.txt --attach report.pdf

初回実行時はブラウザが開き、Google アカウントでの許可を求められる。
許可後のトークンは token_gmail.json に保存され、次回以降は自動で使われる。
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import sys
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 送信のみの最小権限
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = Path(__file__).resolve().parent
# 4-3-2_4 とは別の Google アカウント用の OAuth クライアント
CREDENTIALS_FILE = BASE_DIR.parent / "_json" / "credentials_gmail.json"
# トークンもこのフォルダ専用 (tool の token_calendar.json とは別)
TOKEN_FILE = BASE_DIR / "token_gmail.json"


def get_credentials() -> Credentials:
    """保存済みトークンを読み込み、無効なら更新または再認証する。"""
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
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            print("ブラウザで「送信元にしたい Google アカウント」を選んで許可してください。")
            # select_account: ブラウザでログイン中のアカウントに自動で決まらないよう、毎回選択画面を出す
            creds = flow.run_local_server(port=0, prompt="select_account consent")
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def build_message(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[Path] | None = None,
    html: bool = False,
) -> EmailMessage:
    """送信用の EmailMessage を組み立てる。From は認証したアカウントが自動で入る。"""
    msg = EmailMessage()
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject

    if html:
        msg.set_content("HTML 形式のメールです。HTML 表示に対応したメーラーでご覧ください。")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    for path in attachments or []:
        if not path.is_file():
            raise FileNotFoundError(f"添付ファイルが見つかりません: {path}")
        ctype, encoding = mimetypes.guess_type(path.name)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(
            path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name
        )

    return msg


def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[Path] | None = None,
    html: bool = False,
) -> dict:
    """メールを送信し、Gmail API のレスポンス (id, threadId など) を返す。"""
    service = build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)
    msg = build_message(to, subject, body, cc, bcc, attachments, html)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gmail API でメールを送信します。")
    p.add_argument("--to", nargs="+", required=True, help="宛先 (複数可)")
    p.add_argument("--cc", nargs="+", default=[], help="CC (複数可)")
    p.add_argument("--bcc", nargs="+", default=[], help="BCC (複数可)")
    p.add_argument("--subject", required=True, help="件名")
    body = p.add_mutually_exclusive_group(required=True)
    body.add_argument("--body", help="本文 (文字列)")
    body.add_argument("--body-file", type=Path, help="本文を読み込むファイル (UTF-8)")
    p.add_argument("--html", action="store_true", help="本文を HTML として送信する")
    p.add_argument("--attach", nargs="+", type=Path, default=[], help="添付ファイル (複数可)")
    p.add_argument("-y", "--yes", action="store_true", help="送信前の確認を省略する")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    body = args.body if args.body is not None else args.body_file.read_text(encoding="utf-8")

    print("=== 送信内容 ===")
    print(f"To     : {', '.join(args.to)}")
    if args.cc:
        print(f"Cc     : {', '.join(args.cc)}")
    if args.bcc:
        print(f"Bcc    : {', '.join(args.bcc)}")
    print(f"Subject: {args.subject}")
    if args.attach:
        print(f"Attach : {', '.join(str(a) for a in args.attach)}")
    print("---")
    print(body)
    print("================")

    if not args.yes and input("送信しますか? [y/N]: ").strip().lower() != "y":
        print("送信を中止しました。")
        return 1

    try:
        result = send_email(
            to=args.to,
            subject=args.subject,
            body=body,
            cc=args.cc,
            bcc=args.bcc,
            attachments=args.attach,
            html=args.html,
        )
    except HttpError as e:
        print(f"送信に失敗しました: {e}", file=sys.stderr)
        return 1

    print(f"送信しました。Message ID: {result.get('id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
