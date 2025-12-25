import os
from dotenv import load_dotenv

from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

def _must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

OPENAI_API_KEY = _must_env("OPENAI_API_KEY")
PINECONE_API_KEY = _must_env("PINECONE_API_KEY")
PINECONE_INDEX = _must_env("PINECONE_INDEX")

NAMESPACE_PREFIX = os.getenv("PINECONE_NAMESPACE_PREFIX", "dev")
TZ = os.getenv("TZ", "Asia/Taipei")

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

pc = Pinecone(api_key=PINECONE_API_KEY)
pc_index = pc.Index(PINECONE_INDEX)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def ns_for_user(user_id: str) -> str:
    # e.g. mem_test:user:willy:mem
    return f"{NAMESPACE_PREFIX}:user:{user_id}:mem"
