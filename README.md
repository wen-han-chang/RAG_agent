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

RAG_AGENT/
├── app/
│   ├── __init__.py        # Python package 宣告
│   ├── agent.py           # 核心 RAG Agent（對話流程主控）
│   ├── chat_cli.py        # CLI 測試工具（不經 HTTP，直接測 agent）
│   ├── clients.py         # OpenAI / Pinecone client 初始化
│   ├── config.py          # 讀取 .env、集中管理設定
│   ├── memory_store.py    # 長期記憶（Pinecone 向量儲存 / 查詢）
│   ├── reminder.py        # 吃藥提醒邏輯（時間判斷、停止條件）
│   ├── state_store.py     # 提醒狀態管理（是否已提醒 / 是否已吃藥）
│   ├── server.py          # Flask API Server 入口
│   └── __pycache__/       # Python 快取（不應提交）
│
├── script/                # 輔助腳本（測試 / 資料初始化等）
│
├── .env                   # 私密設定
├── requirements.txt       # Python 套件清單
└── readme.md              # 專案說明文件


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

