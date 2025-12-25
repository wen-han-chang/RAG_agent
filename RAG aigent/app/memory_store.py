import time
import uuid
from typing import List, Dict, Any, Optional

from app.clients import pc_index, openai_client, ns_for_user, EMBED_MODEL

def embed(text: str) -> List[float]:
    return openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    ).data[0].embedding

def upsert_memory(
    user_id: str,
    text: str,
    mtype: str,
    tags: Optional[List[str]] = None,
    importance: int = 1
) -> str:
    vec = embed(text)
    mem_id = f"mem_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    meta = {
        "type": mtype,            # profile / preference / event
        "text": text,
        "tags": tags or [],
        "importance": int(importance),
        "ts": int(time.time()),
        "user_id": user_id,
    }

    pc_index.upsert(
        vectors=[{"id": mem_id, "values": vec, "metadata": meta}],
        namespace=ns_for_user(user_id)
    )
    return mem_id

def query_memory(user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    qv = embed(query)
    res = pc_index.query(
        namespace=ns_for_user(user_id),
        vector=qv,
        top_k=top_k,
        include_metadata=True
    )

    matches = getattr(res, "matches", None) or (res.get("matches", []) if isinstance(res, dict) else [])
    hits: List[Dict[str, Any]] = []
    for m in matches:
        score = getattr(m, "score", None) if not isinstance(m, dict) else m.get("score")
        md = getattr(m, "metadata", None) if not isinstance(m, dict) else m.get("metadata", {})
        mid = getattr(m, "id", None) if not isinstance(m, dict) else m.get("id")

        if not md:
            continue
        hits.append({
            "id": mid,
            "score": float(score) if score is not None else None,
            "type": md.get("type"),
            "text": md.get("text"),
            "tags": md.get("tags", []),
            "importance": md.get("importance", 1),
            "ts": md.get("ts"),
        })
    return hits

def stats(user_id: str) -> dict:
    s = pc_index.describe_index_stats()
    ns = ns_for_user(user_id)
    namespaces = getattr(s, "namespaces", None) if not isinstance(s, dict) else s.get("namespaces", {})
    return {"namespace": ns, "count": (namespaces.get(ns, {}) or {}).get("vector_count", 0)}

def fetch_user_name(user_id: str) -> Optional[str]:
    # 用語意查詢去撈「名字」記憶（只取最可信的一條）
    hits = query_memory(user_id, query="使用者名字是什麼？他的名字", top_k=8)
    for h in hits:
        tags = h.get("tags", []) or []
        txt = (h.get("text") or "").strip()
        if "name" in tags and "使用者名字是" in txt:
            return txt.split("使用者名字是", 1)[-1].strip() or None
    return None
