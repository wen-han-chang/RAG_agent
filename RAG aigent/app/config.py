import os
from dotenv import load_dotenv

load_dotenv()  # 讓 .env 進入 os.environ

def require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

OPENAI_API_KEY = require_env("OPENAI_API_KEY")
PINECONE_API_KEY = require_env("PINECONE_API_KEY")
PINECONE_INDEX = require_env("PINECONE_INDEX")

PINECONE_NAMESPACE_PREFIX = os.getenv("PINECONE_NAMESPACE_PREFIX", "dev")

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

TZ = os.getenv("TZ", "Asia/Taipei")

# 記憶最多取幾條
MEM_TOP_K = int(os.getenv("MEM_TOP_K", "5"))

# 對話歷史保留幾輪（user+assistant 算兩筆）
HISTORY_MAX_TURNS = int(os.getenv("HISTORY_MAX_TURNS", "10"))

# 吃藥提醒（秒）
REMIND_INTERVAL_SEC = int(os.getenv("REMIND_INTERVAL_SEC", "1800"))
