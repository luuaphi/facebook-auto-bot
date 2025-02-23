import requests
import json
import os
from flask import Flask, request

app = Flask(__name__)

# Lấy Access Token và Page ID từ biến môi trường
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "YOUR_VERIFY_TOKEN")
FB_API_URL = "https://graph.facebook.com/v19.0"

# Cấu hình bật/tắt từng tính năng
auto_post = True
auto_reply_msg = True
auto_reply_comment = True

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == VERIFY_TOKEN:
            return challenge
        return "Invalid verification token"
    elif request.method == "POST":
        data = request.get_json()
        if "entry" in data:
            for entry in data["entry"]:
                for event in entry.get("messaging", []):
                    if "message" in event and auto_reply_msg:
                        handle_message(event)
                for comment in entry.get("changes", []):
                    if comment.get("field") == "feed" and "message" in comment["value"] and auto_reply_comment:
                        handle_comment(comment["value"])
        return "EVENT_RECEIVED", 200

@app.route("/toggle", methods=["POST"])
def toggle():
    global auto_post, auto_reply_msg, auto_reply_comment
    data = request.get_json()
    if "auto_post" in data:
        auto_post = data["auto_post"]
    if "auto_reply_msg" in data:
        auto_reply_msg = data["auto_reply_msg"]
    if "auto_reply_comment" in data:
        auto_reply_comment = data["auto_reply_comment"]
    return json.dumps({"auto_post": auto_post, "auto_reply_msg": auto_reply_msg, "auto_reply_comment": auto_reply_comment}), 200

# Xử lý tin nhắn Messenger
def handle_message(event):
    sender_id = event["sender"]["id"]
    message_text = event["message"].get("text", "")
    response_text = f"Cảm ơn bạn đã nhắn tin! Bạn hỏi: {message_text}"  # Trả lời tự động
    send_message(sender_id, response_text)

# Xử lý bình luận
def handle_comment(comment):
    comment_id = comment["id"]
    message_text = comment["message"]
    response_text = f"Cảm ơn bạn đã bình luận! Bạn nói: {message_text}"  # Trả lời tự động
    send_comment(comment_id, response_text)

# Gửi tin nhắn Messenger
def send_message(recipient_id, text):
    url = f"{FB_API_URL}/me/messages?access_token={ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload)

# Gửi trả lời bình luận
def send_comment(comment_id, text):
    url = f"{FB_API_URL}/{comment_id}/comments?access_token={ACCESS_TOKEN}"
    payload = {"message": text}
    requests.post(url, json=payload)

# Đăng bài lên Fanpage
def post_to_facebook(message):
    if auto_post:
        url = f"{FB_API_URL}/{PAGE_ID}/feed?access_token={ACCESS_TOKEN}"
        payload = {"message": message}
        response = requests.post(url, json=payload)
        return response.json()
    return {"status": "Auto post is disabled"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

