"""
upload/ フォルダを監視し、ファイルが追加されたら自動で Google Drive にアップロードする。

使い方:
  1. DRIVE_FOLDER_ID を設定する（Drive フォルダ URL の末尾の文字列）
     例) https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMd... → "1BxiMVs0XRA5nFMd..."
  2. python watcher.py を実行する
  3. upload/ フォルダにファイルを置くだけで自動アップロードされる
  4. Ctrl+C で停止
"""

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from upload_to_drive import authenticate, upload_file
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

WATCH_DIR = Path(__file__).parent / "upload"
DRIVE_FOLDER_ID = "YOUR_FOLDER_ID_HERE"  # ← ここに Drive フォルダ ID を設定


def wait_for_file_ready(path: Path, timeout: int = 60) -> bool:
    """ファイルの書き込みが完了するまでサイズの安定を待つ。"""
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
    def __init__(self, service):
        self.service = service
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
            result = upload_file(self.service, str(path), drive_folder_id=DRIVE_FOLDER_ID)
            print(f"[完了] {result['name']}")
            print(f"       {result.get('webViewLink', '')}")
        except (FileNotFoundError, HttpError) as e:
            print(f"[エラー] {path.name}: {e}")
        finally:
            self._in_progress.discard(path)

    def on_created(self, event):
        self._upload(Path(event.src_path))

    def on_moved(self, event):
        # Finder からドラッグ&ドロップした場合も検出できるよう移動先を処理する
        self._upload(Path(event.dest_path))


def main():
    if DRIVE_FOLDER_ID == "YOUR_FOLDER_ID_HERE":
        print("エラー: watcher.py の DRIVE_FOLDER_ID を設定してください。")
        print("  例) https://drive.google.com/drive/folders/<この部分>")
        return

    WATCH_DIR.mkdir(exist_ok=True)
    print(f"監視フォルダ : {WATCH_DIR}")
    print(f"アップロード先: https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}")

    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    observer = Observer()
    observer.schedule(UploadHandler(service), str(WATCH_DIR), recursive=False)
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
