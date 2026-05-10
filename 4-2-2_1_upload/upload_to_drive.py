"""
Google Drive API を使ってローカルファイルをアップロードするスクリプト（サービスアカウント認証）

事前準備:
1. pip install google-auth google-auth-httplib2 google-api-python-client
2. サービスアカウントキー JSON をこのスクリプトと同じフォルダに配置済み
3. アップロード先の共有ドライブにサービスアカウントを「コンテンツ管理者」で追加する
"""

import sys
import mimetypes
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]

# スクリプトと同じフォルダにある JSON キーを自動検索
_script_dir = Path(__file__).parent
_key_candidates = [p for p in _script_dir.glob("*.json") if "token" not in p.name]
SERVICE_ACCOUNT_FILE = str(_key_candidates[0]) if _key_candidates else "service_account.json"


def authenticate():
    """サービスアカウントキーで認証し、認証情報を返す。"""
    if not Path(SERVICE_ACCOUNT_FILE).exists():
        print(f"エラー: サービスアカウントキーが見つかりません: {SERVICE_ACCOUNT_FILE}")
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    print(f"認証完了: {Path(SERVICE_ACCOUNT_FILE).name}")
    return creds


def upload_file(
    service,
    local_path: str,
    drive_folder_id: str = None,
    drive_filename: str = None,
) -> dict:
    """ローカルファイルを Google Drive（共有ドライブ対応）にアップロードする。"""
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {local_path}")

    filename = drive_filename or path.name
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    file_metadata = {"name": filename}
    if drive_folder_id:
        file_metadata["parents"] = [drive_folder_id]

    media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)

    print(f"アップロード中: {path.name} ({mime_type})")
    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink",
            supportsAllDrives=True,  # 共有ドライブ対応
        )
        .execute()
    )

    return file


def upload_folder(
    service,
    local_dir: str,
    drive_folder_id: str = None,
    recursive: bool = True,
) -> list:
    """ローカルフォルダ内のファイルを Google Drive にアップロードする。"""
    dir_path = Path(local_dir)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"ディレクトリが見つかりません: {local_dir}")

    uploaded_files = []

    for item in dir_path.iterdir():
        if item.is_file():
            try:
                result = upload_file(service, str(item), drive_folder_id)
                uploaded_files.append(result)
                print(f"  完了: {result['name']} (ID: {result['id']})")
            except HttpError as e:
                print(f"  失敗: {item.name} - {e}")
        elif item.is_dir() and recursive:
            sub_folder = (
                service.files()
                .create(
                    body={
                        "name": item.name,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [drive_folder_id] if drive_folder_id else [],
                    },
                    fields="id, name",
                    supportsAllDrives=True,
                )
                .execute()
            )
            print(f"フォルダ作成: {sub_folder['name']} (ID: {sub_folder['id']})")
            sub_files = upload_folder(service, str(item), sub_folder["id"], recursive)
            uploaded_files.extend(sub_files)

    return uploaded_files


def main():
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    # ========================================
    # 使い方の例 — 必要に応じてコメントを外して使用してください
    # FOLDER_ID: Drive フォルダの URL 末尾の ID
    # 例) https://drive.google.com/drive/folders/XXXXXXXXXX → "XXXXXXXXXX"
    # ========================================

    # 例1: 単一ファイルを特定フォルダにアップロード
    # result = upload_file(service, "sample.txt", drive_folder_id="YOUR_FOLDER_ID")
    # print(result)

    # 例2: フォルダ内の全ファイルをアップロード（サブフォルダ含む）
    # upload_folder(service, "./my_folder", drive_folder_id="YOUR_FOLDER_ID")

    # --- コマンドライン引数からファイルパスとフォルダIDを受け取る ---
    if len(sys.argv) < 2:
        print("使い方: python upload_to_drive.py <ファイルパス> [フォルダID]")
        print("例:     python upload_to_drive.py ./photo.jpg 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")
        sys.exit(0)

    local_path = sys.argv[1]
    folder_id = sys.argv[2] if len(sys.argv) >= 3 else None

    try:
        result = upload_file(service, local_path, drive_folder_id=folder_id)
        print("\nアップロード成功!")
        print(f"  ファイル名 : {result['name']}")
        print(f"  ファイル ID: {result['id']}")
        print(f"  Drive URL  : {result.get('webViewLink', 'N/A')}")
    except (FileNotFoundError, HttpError) as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
