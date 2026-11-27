# Gmail 送信スクリプト

Gmail API を使って、指定した宛先にメールを送信します。

## 準備

このスクリプトは 4-3-2_4 とは**別の Google アカウント**を送信元にする前提です。認証ファイルもトークンも 4-3-2_4 とは分けています。

| | tool（旧 4-3-2_4） | 4-3-2_5（これ） |
|---|---|---|
| OAuth クライアント | `_json/credentials.json` | `_json/credentials_gmail.json` |
| トークン | `tool/token_calendar.json` | `4-3-2_5/token_gmail.json` |

1. **送信元にしたい Google アカウント**で [Google Cloud Console](https://console.cloud.google.com/) にログインし、新しいプロジェクトを作成
2. そのプロジェクトで **Gmail API** を有効化
3. OAuth 同意画面を設定（User Type は「外部」、テストモードのままで OK）し、「テストユーザー」に送信元アカウントを追加
4. 「認証情報」→「OAuth クライアント ID を作成」→ 種類「デスクトップ アプリ」で作成し、JSON をダウンロード
5. ダウンロードした JSON を `../_json/credentials_gmail.json` という名前で保存
6. ライブラリをインストール

```bash
pip install -r requirements.txt
```

初回実行時にブラウザでアカウント選択画面が出ます。**送信元にしたいアカウントを選んで**許可してください（ブラウザで 4-3-2_4 のアカウントにログインしていても、選択画面で切り替えられます）。
許可後のトークンは `token_gmail.json` に保存されます（Git 管理外）。権限は送信のみ（`gmail.send`）です。

間違ったアカウントで許可してしまった場合は、`token_gmail.json` を削除してもう一度実行すれば選び直せます。

## 使い方

```bash
python send_gmail.py --to someone@example.com --subject "件名" --body "本文です"
```

| オプション | 説明 |
|---|---|
| `--to` | 宛先（必須・複数可） |
| `--cc` / `--bcc` | CC / BCC（複数可） |
| `--subject` | 件名（必須） |
| `--body` / `--body-file` | 本文の文字列 / 本文ファイル（どちらか必須） |
| `--html` | 本文を HTML として送信 |
| `--attach` | 添付ファイル（複数可） |
| `-y` | 送信前の確認を省略 |

送信前に内容が表示され、`y` を入力すると送信されます。

## 他のコードから使う

```python
from send_gmail import send_email
send_email(to=["someone@example.com"], subject="件名", body="本文")
```
