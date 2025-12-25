# RAG Agent（Elderly Care Chatbot）

這是一個基於 **RAG（Retrieval-Augmented Generation）** 的聊天代理系統，  
專為 **年長者陪伴、健康提醒、長期記憶管理** 所設計。

後端以 **Python + Flask** 實作，可由 **Node.js / Web / App** 透過 HTTP 呼叫。

---

## 功能特色

- ✅ **溫暖陪伴式對話**（可自動稱呼使用者名字）  
- ✅ **Pinecone 長期記憶**（記錄興趣、習慣、偏好）  
- ✅ **吃藥提醒系統**（每 5 分鐘提醒一次，確認吃藥後自動停止）  
- ✅ **跨裝置整合**（Node.js / Web / App 均可使用）

---

## 專案結構

```
app/
├── agent.py        # 核心對話邏輯
├── memory_store.py # Pinecone 記憶管理
├── state_store.py  # SQLite 吃藥狀態儲存
├── reminder.py     # 提醒邏輯
├── server.py       # Flask API 入口
├── chat_cli.py     # CLI 測試工具
└── clients.py      # OpenAI / Pinecone 客戶端
```

---

## 環境需求

- Python >= 3.10  
- Pinecone 帳號  
- OpenAI API Key  

---

## 安裝

```bash
pip install -r requirements.txt
```

---

## 環境變數（.env）

```env
OPENAI_API_KEY=sk-xxxx
PINECONE_API_KEY=xxxx
PINECONE_INDEX=chatbot-index
PINECONE_NAMESPACE_PREFIX=mem_test
CHAT_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
TZ=Asia/Taipei
```

---

## 啟動 Server

```bash
python -m app.server
```

成功後會看到：

```
Running on http://0.0.0.0:8000
```

---

## API 使用方式

### POST /chat

#### Request

```json
{
  "user_id": "willy",
  "text": "我喜歡跑步"
}
```

#### Response

```json
{
  "reply": "很好呢，Willy！跑步真的很棒～"
}
```

---

## Node.js 範例

```js
import axios from "axios";

const res = await axios.post("http://SERVER_IP:8000/chat", {
  user_id: "willy",
  text: "我喜歡在河邊慢跑"
});

console.log(res.data.reply);
```

---

## 注意事項

- Flask 為開發用伺服器，正式環境請使用 **gunicorn / uvicorn**  
- Pinecone namespace 會依 `user_id` 自動分隔  
- 使用者中斷後，長期記憶仍會保留  

