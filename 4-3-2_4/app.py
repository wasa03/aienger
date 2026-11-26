"""
業務効率化ツール(ローカルWebサイト)

起動: start.command をダブルクリック
      (または .venv/bin/python app.py を実行し、http://127.0.0.1:5050 を開く)

ツールを増やすときは TOOLS に1行追加し、ルートとテンプレートを足す。
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request

from create_meet import create_meet_event
from create_zoom_meeting import create_meeting, get_access_token

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

# 左のメニューに出すツール一覧
TOOLS = [
    {"endpoint": "zoom", "name": "Zoom会議を作る", "icon": "🎥"},
    {"endpoint": "meet", "name": "Google Meetを作る", "icon": "📹"},
    {"endpoint": "sircars", "name": "SIRCARS定例", "icon": "📅"},
]

# SIRCARS定例ツールの場所(設定・認証は元のフォルダのものをそのまま使う)
SIRCARS_DIR = os.environ.get("SIRCARS_DIR", os.path.expanduser("~/Git/SIRCARS-regular-mtg"))
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]


def load_teirei():
    """元フォルダの teirei.py / config.py を読み込む(毎回読み直すので設定変更がすぐ反映される)。"""
    import importlib
    import sys

    if not os.path.isfile(os.path.join(SIRCARS_DIR, "teirei.py")):
        raise FileNotFoundError(f"SIRCARS定例ツールが見つかりません: {SIRCARS_DIR}")
    if SIRCARS_DIR not in sys.path:
        sys.path.insert(0, SIRCARS_DIR)
    import config
    import teirei

    importlib.reload(config)
    importlib.reload(teirei)
    return teirei, config


@app.context_processor
def inject_tools():
    return {"tools": TOOLS}


@app.route("/")
def index():
    return render_template("index.html")


def default_start() -> str:
    """初期値: 次の正時(1時間後)"""
    t = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return t.strftime("%Y-%m-%dT%H:%M")


@app.route("/zoom", methods=["GET", "POST"])
def zoom():
    form = {
        "topic": request.form.get("topic", "").strip(),
        "start": request.form.get("start") or default_start(),
        "duration": request.form.get("duration") or "60",
    }
    result = None
    error = None

    if request.method == "POST":
        try:
            start_time = datetime.strptime(form["start"], "%Y-%m-%dT%H:%M")
            duration = int(form["duration"])
            if duration <= 0:
                raise ValueError("時間は1分以上にしてください")

            token = get_access_token(
                os.environ["ZOOM_ACCOUNT_ID"],
                os.environ["ZOOM_CLIENT_ID"],
                os.environ["ZOOM_CLIENT_SECRET"],
            )
            m = create_meeting(
                token,
                topic=form["topic"] or "ミーティング",
                start_time=start_time,
                duration=duration,
                timezone="Asia/Tokyo",
            )
            result = {
                "topic": m["topic"],
                "start": start_time.strftime("%Y年%m月%d日 %H:%M"),
                "duration": duration,
                "id": m["id"],
                "id_display": f"{str(m['id'])[:3]} {str(m['id'])[3:7]} {str(m['id'])[7:]}",
                "password": m.get("password", ""),
                "join_url": m["join_url"],
            }
        except KeyError as e:
            error = f".env に {e} が設定されていません"
        except ValueError as e:
            error = f"入力を確認してください: {e}"
        except Exception as e:  # Zoom側のエラーなど
            error = str(e)

    return render_template("zoom.html", form=form, result=result, error=error)


@app.route("/meet", methods=["GET", "POST"])
def meet():
    form = {
        "topic": request.form.get("topic", "").strip(),
        "start": request.form.get("start") or default_start(),
        "duration": request.form.get("duration") or "60",
    }
    result = None
    error = None

    if request.method == "POST":
        try:
            start_time = datetime.strptime(form["start"], "%Y-%m-%dT%H:%M")
            duration = int(form["duration"])
            if duration <= 0:
                raise ValueError("時間は1分以上にしてください")

            r = create_meet_event(form["topic"] or "ミーティング", start_time, duration)
            if not r["meet_url"]:
                raise RuntimeError("予定は作成されましたが、Meetのリンクがまだ発行されていません。カレンダーの予定を確認してください。")
            result = {**r, "start": start_time.strftime("%Y年%m月%d日 %H:%M"), "duration": duration}
        except FileNotFoundError as e:
            error = str(e)
        except ValueError as e:
            error = f"入力を確認してください: {e}"
        except Exception as e:  # Google側のエラーなど
            error = str(e)

    return render_template("meet.html", form=form, result=result, error=error)


@app.route("/sircars", methods=["GET", "POST"])
def sircars():
    """日時入力 → 確認画面 → 実行(カレンダー登録・招待メール・ChatWork投稿)"""
    start_str = request.form.get("start") or default_start()
    action = request.form.get("action", "")
    ctx = {"start": start_str, "preview": None, "result": None, "error": None, "settings": None}

    try:
        teirei, config = load_teirei()
        ctx["settings"] = {
            "title": config.MEETING_TITLE,
            "duration": config.MEETING_DURATION_MINUTES,
            "invitees": config.INVITEES,
            "mentions": [m["name"] for m in config.CHATWORK_MENTIONS],
        }
    except Exception as e:
        ctx["error"] = str(e)
        return render_template("sircars.html", **ctx)

    if request.method == "POST":
        try:
            start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
            end = start + timedelta(minutes=config.MEETING_DURATION_MINUTES)
            label = f"{start:%Y年%m月%d日}({WEEKDAYS_JP[start.weekday()]}) {start:%H:%M}〜{end:%H:%M}"

            if action == "preview":
                if start < datetime.now():
                    raise ValueError("過去の日時になっています")
                ctx["preview"] = {
                    "label": label,
                    "message": teirei.format_message(start, end, "(ここにMeetのリンクが入ります)"),
                }

            elif action == "run":
                creds = teirei.get_credentials()
                event = teirei.create_meet_event(creds, start, end)
                meet_url = teirei.extract_meet_url(event)
                if not meet_url:
                    raise RuntimeError("予定は作成されましたが、Meetのリンクを取得できませんでした。カレンダーを確認してください。")
                message = teirei.format_message(start, end, meet_url)
                result = {"label": label, "meet_url": meet_url, "event_url": event.get("htmlLink", ""),
                          "message": message, "chatwork_ok": False, "chatwork_error": ""}
                try:
                    teirei.send_chatwork(message)
                    result["chatwork_ok"] = True
                except Exception as e:
                    # 予定と招待は済んでいるので、手動で貼れるように本文を出す
                    result["chatwork_error"] = str(e)
                ctx["result"] = result
        except ValueError as e:
            ctx["error"] = f"入力を確認してください: {e}"
        except Exception as e:
            ctx["error"] = str(e)

    return render_template("sircars.html", **ctx)


if __name__ == "__main__":
    # 127.0.0.1 = このMacからだけ開ける(ほかの人からは見えない)
    app.run(host="127.0.0.1", port=5050, debug=False)
