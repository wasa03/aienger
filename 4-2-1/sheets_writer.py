"""
Google Sheets にサービスアカウントでデータを書き込むサンプル。

前提:
  pip install google-auth google-auth-httplib2 google-api-python-client

サービスアカウントの準備:
  1. Google Cloud Console でサービスアカウントを作成
  2. JSON キーをダウンロードして SERVICE_ACCOUNT_FILE に指定
  3. 対象スプレッドシートをサービスアカウントのメールアドレスに共有（編集者権限）
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ---- 設定 ----
SERVICE_ACCOUNT_FILE = "level-racer-495902-u8-c2342607c89b.json"   # サービスアカウントの JSON キーファイル
SPREADSHEET_ID = "1x_pcbcC_4i9HaPzLdydQLYJAJ0uOAjpFsfnefcix5iQ"          # URL の /d/<ここ>/edit
SHEET_NAME = "Sheet1"                            # タブ名

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def write_rows(service, range_name: str, values: list[list]) -> dict:
    """指定範囲にデータを上書き（valueInputOption=USER_ENTERED）。"""
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    return result


def append_rows(service, range_name: str, values: list[list]) -> dict:
    """テーブルの末尾にデータを追記。"""
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    return result


def main():
    service = get_service()

    # ヘッダーと 2 行のデータを A1 から書き込む
    sample_data = [
        ["名前", "スコア", "日付"],
        ["Alice", 95, "2026-05-10"],
        ["Bob", 82, "2026-05-10"],
    ]
    range_name = f"{SHEET_NAME}!A1"

    result = write_rows(service, range_name, sample_data)
    print(f"更新セル数: {result.get('updatedCells')}")

    # 追記の例
    new_row = [["Carol", 78, "2026-05-10"]]
    append_result = append_rows(service, f"{SHEET_NAME}!A1", new_row)
    print(f"追記先: {append_result['updates'].get('updatedRange')}")


if __name__ == "__main__":
    main()
