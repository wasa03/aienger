from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = "../_json/study-495902-239105e792f5.json"
FOLDER_ID = "0AHjUFAdXZnnuUk9PVA"
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def get_services():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    drive = build("drive", "v3", credentials=creds)
    docs = build("docs", "v1", credentials=creds)
    return drive, docs


def create_document(drive, title):
    # Drive API で共有ドライブ内に Google Docs ファイルを作成
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [FOLDER_ID],
    }
    file = (
        drive.files()
        .create(
            body=file_metadata,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    return file["id"]


def insert_text(docs, doc_id, text):
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": text,
            }
        }
    ]
    docs.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()


def main():
    title = input("ドキュメントのタイトルを入力してください: ")
    text = input("挿入するテキストを入力してください: ")

    try:
        drive, docs = get_services()

        doc_id = create_document(drive, title)
        print(f"ドキュメントを作成しました（ID: {doc_id}）")

        insert_text(docs, doc_id, text)
        print("テキストを挿入しました")

        print(f"URL: https://docs.google.com/document/d/{doc_id}/edit")

    except HttpError as e:
        print(f"API エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
