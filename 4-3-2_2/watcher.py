"""
upload/ フォルダを監視し、ファイルが追加されたら自動で Google Drive にアップロードする。
アップロードのたびに Google Docs のアップロード履歴ドキュメントへ記録する。

使い方:
  1. python watcher.py を実行する
  2. upload/ フォルダにファイルを置くだけで自動アップロードされる
  3. Ctrl+C で停止
"""

import mimetypes
import time
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

SERVICE_ACCOUNT_FILE = "../_json/study-495902-239105e792f5.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]
WATCH_DIR = Path(__file__).parent / "upload"
DRIVE_FOLDER_ID = "0AHjUFAdXZnnuUk9PVA"


def get_services():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    return drive, docs


def upload_file(drive, local_path: str) -> dict:
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {local_path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
    file = (
        drive.files()
        .create(
            body={"name": path.name, "parents": [DRIVE_FOLDER_ID]},
            media_body=media,
            fields="id, name, webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )
    return file


def create_history_doc(drive, docs) -> str:
    title = f"アップロード履歴 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    file = (
        drive.files()
        .create(
            body={
                "name": title,
                "mimeType": "application/vnd.google-apps.document",
                "parents": [DRIVE_FOLDER_ID],
            },
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    doc_id = file["id"]

    header = f"アップロード履歴\n開始日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"insertText": {"location": {"index": 1}, "text": header}}]},
    ).execute()

    return doc_id


def append_history(docs, doc_id, filename, url):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 挿入前にドキュメント末尾のインデックスを取得
    doc = docs.documents().get(documentId=doc_id).execute()
    body_content = doc.get("body", {}).get("content", [])
    insert_index = body_content[-1]["startIndex"]

    line1 = f"[{timestamp}] {filename}\n"
    link_text = url if url else "(URL なし)"
    suffix = "\n\n"

    url_start = insert_index + len(line1)
    url_end = url_start + len(link_text)

    requests = [
        {
            "insertText": {
                "endOfSegmentLocation": {"segmentId": ""},
                "text": line1 + link_text + suffix,
            }
        },
    ]
    if url:
        requests.append({
            "updateTextStyle": {
                "range": {"startIndex": url_start, "endIndex": url_end},
                "textStyle": {"link": {"url": url}},
                "fields": "link",
            }
        })

    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests},
    ).execute()


def wait_for_file_ready(path: Path, timeout: int = 60) -> bool:
    prev_size = -1
    for _ in range(timeout):
        try:
            current_size = path.stat().st_size
            if current_size == prev_size:
                return True
            prev_size = current_size
        except FileNotFoundError:
            return False
        time.sleep(1)
    return True


class UploadHandler(FileSystemEventHandler):
    def __init__(self, drive, docs, doc_id):
        self.drive = drive
        self.docs = docs
        self.doc_id = doc_id
        self._in_progress: set[Path] = set()

    def _upload(self, path: Path):
        if path in self._in_progress or path.is_dir() or path.name.startswith("."):
            return
        self._in_progress.add(path)
        try:
            print(f"\n[検出] {path.name} — 書き込み完了を待機中...")
            if not wait_for_file_ready(path):
                print(f"[スキップ] ファイルが見つかりません: {path.name}")
                return
            result = upload_file(self.drive, str(path))
            url = result.get("webViewLink", "")
            print(f"[完了] {result['name']}")
            print(f"       {url}")

            append_history(self.docs, self.doc_id, result["name"], url)
            print(f"[履歴記録] ドキュメントに追記しました")
        except (FileNotFoundError, HttpError) as e:
            print(f"[エラー] {path.name}: {e}")
        finally:
            self._in_progress.discard(path)

    def on_created(self, event):
        self._upload(Path(event.src_path))

    def on_moved(self, event):
        self._upload(Path(event.dest_path))


def main():
    WATCH_DIR.mkdir(exist_ok=True)

    drive, docs = get_services()
    doc_id = create_history_doc(drive, docs)
    history_url = f"https://docs.google.com/document/d/{doc_id}/edit"

    print(f"監視フォルダ : {WATCH_DIR}")
    print(f"アップロード先: https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}")
    print(f"履歴ドキュメント: {history_url}")

    observer = Observer()
    observer.schedule(UploadHandler(drive, docs, doc_id), str(WATCH_DIR), recursive=False)
    observer.start()
    print("\nupload/ にファイルを置くと自動でアップロードします。Ctrl+C で停止。\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止しました。")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
