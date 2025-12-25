from flask import Flask, request, jsonify
from flask_cors import CORS

from app.agent import respond

app = Flask(__name__)
CORS(app)

# ✅ health check：瀏覽器打開 http://127.0.0.1:8000/ 會看到 JSON
@app.get("/")
def health():
    return jsonify({"ok": True, "service": "rag-agent", "routes": ["POST /chat"]})

@app.route("/chat", methods=["POST", "GET"])
def chat():
    if request.method == "GET":
        return jsonify({"ok": False, "hint": "Use POST /chat with JSON: {user_id, text}"}), 405

    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "willy").strip()
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"ok": False, "error": "text is required"}), 400

    # server 模式：history 建議由 Node 端維護；這裡先用空 history（長期記憶由 Pinecone 補）
    reply = respond(user_id=user_id, user_text=text, history=[])
    return jsonify({"ok": True, "user_id": user_id, "reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
