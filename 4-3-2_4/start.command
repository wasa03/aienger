#!/bin/zsh
# ダブルクリックで業務効率化ツールを起動する。止めるときはこのウィンドウを閉じる。
cd "$(dirname "$0")"

URL="http://127.0.0.1:5050"

# すでに起動していればブラウザを開くだけ
if curl -s -o /dev/null "$URL"; then
  open "$URL"
  exit 0
fi

# 初回は必要な部品を準備
if [ ! -x .venv/bin/python ]; then
  echo "初回の準備をしています…"
  python3 -m venv .venv && .venv/bin/pip install -q requests python-dotenv flask google-auth google-auth-oauthlib google-api-python-client
fi

echo "業務効率化ツールを起動しました: $URL"
echo "終了するときは、このウィンドウを閉じてください。"
(sleep 1.5 && open "$URL") &
.venv/bin/python app.py
