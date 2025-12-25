import json
import re
from typing import List, Dict, Optional

from app.clients import openai_client, CHAT_MODEL
from app.memory_store import query_memory, upsert_memory, fetch_user_name
from app.reminder import should_remind_now, reminder_text, user_ack_med
from app.state_store import mark_done

SYSTEM_PROMPT = """你是一位溫暖、耐心、適合陪伴年長者的居家照護聊天助理。
原則：
- 語氣溫柔、句子不要太長、一步一步說清楚。
- 如果有「記憶內容」請自然地融入，不要說「我從資料庫查到」。
- 不確定就用委婉方式詢問，不要硬猜。
- 健康提醒要溫馨、不恐嚇；涉及醫療建議要保守，鼓勵詢問醫師/家屬。
"""

NAME_BAD_WORDS = ["什麼", "甚麼", "不知道", "不清楚", "忘了", "名字", "叫什麼", "叫甚麼"]

def build_memory_context(user_id: str, user_text: str, k: int = 6) -> str:
    hits = query_memory(user_id=user_id, query=user_text, top_k=k)
    if not hits:
        return ""

    # 重要度高的優先
    hits = sorted(hits, key=lambda h: (int(h.get("importance", 1)), int(h.get("ts") or 0)), reverse=True)

    lines = []
    for h in hits[:k]:
        t = h.get("type")
        txt = h.get("text")
        if txt:
            lines.append(f"- ({t}) {txt}")
    if not lines:
        return ""

    return "你已知的使用者相關記憶如下（僅供你生成更貼心回覆使用）：\n" + "\n".join(lines)

def _looks_like_name(name: str) -> bool:
    n = name.strip()
    if not (1 <= len(n) <= 12):
        return False
    if any(w in n for w in NAME_BAD_WORDS):
        return False
    # 避免整句
    if len(n) >= 6 and re.search(r"[，。！？,.!? ]", n):
        return False
    return True

def try_extract_name(user_text: str) -> Optional[str]:
    t = (user_text or "").strip()

    m = re.search(r"(?:我叫|我是|我的名字是)\s*([^\s，。！？,.!?]{1,12})", t)
    if m:
        cand = m.group(1).strip()
        if _looks_like_name(cand):
            return cand
    return None

def store_name_if_any(user_id: str, user_text: str) -> Optional[str]:
    name = try_extract_name(user_text)
    if not name:
        return None
    upsert_memory(user_id, f"使用者名字是{name}", mtype="profile", tags=["name"], importance=3)
    return name

def extract_and_store_memory(user_id: str, user_text: str):
    """
    - 名字用規則先抓（避免「我叫甚麼名字」這種被誤存）
    - 其他用模型抽 0~2 條長期資訊
    """
    if store_name_if_any(user_id, user_text):
        return

    t = (user_text or "").strip()
    prompt = f"""從使用者這句話中，判斷是否有「值得長期記住」的資訊。
只輸出 JSON 陣列（0~2 個元素），每個元素包含：
- type: profile | preference | event
- text: 一句可直接存的記憶（中文）
- tags: 關鍵字陣列（例如 hobby/family/medicine/sport）
- importance: 1~3（越重要越高）

注意：
- 不要把「詢問句」或「反問句」當成事實記憶。
- 不要記錄太短或太泛的話（例如：你好、今天天氣不錯）。
- 只存對未來聊天真的有用、且可能維持一段時間的資訊。

使用者句子：{t}
"""
    try:
        resp = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "你是一個嚴格輸出 JSON 的資訊抽取器。只能輸出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        items = json.loads(raw)
        if not isinstance(items, list):
            return
        for it in items[:2]:
            mtype = it.get("type")
            text = it.get("text")
            tags = it.get("tags", [])
            imp = int(it.get("importance", 1))
            if mtype in ("profile", "preference", "event") and isinstance(text, str) and len(text) >= 6:
                upsert_memory(
                    user_id,
                    text.strip(),
                    mtype=mtype,
                    tags=tags if isinstance(tags, list) else [],
                    importance=max(1, min(3, imp)),
                )
    except Exception:
        return

def call_llm(user_text: str, mem_ctx: str, history: List[Dict[str, str]], name: Optional[str]) -> str:
    sys = SYSTEM_PROMPT
    if name:
        sys += f"\n你正在和使用者{name}對話，請盡量用{name}稱呼對方。"

    msgs = [{"role": "system", "content": sys}]
    if mem_ctx:
        msgs.append({"role": "system", "content": mem_ctx})
    msgs.extend(history[-10:])
    msgs.append({"role": "user", "content": user_text})

    resp = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=msgs,
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()

def is_ask_profile(text: str) -> bool:
    t = (text or "").strip()
    keys = ["你對我的了解", "你對我了解", "你知道我", "我的興趣", "記得我", "你記得我", "我的資料", "你了解我"]
    return any(k in t for k in keys)

def summarize_user(user_id: str) -> str:
    name = fetch_user_name(user_id)
    hits = query_memory(user_id=user_id, query="使用者的興趣、習慣、偏好、家人、健康提醒相關資訊", top_k=12)

    # 過濾掉名字那條（後面會單獨講）
    items = []
    for h in hits:
        txt = (h.get("text") or "").strip()
        tags = h.get("tags", []) or []
        if "name" in tags:
            continue
        if txt:
            items.append(txt)

    # 去重（保留順序）
    seen = set()
    uniq = []
    for x in items:
        if x not in seen:
            uniq.append(x)
            seen.add(x)

    if name and uniq:
        bullet = "\n".join([f"- {x}" for x in uniq[:6]])
        return f"當然可以，{name}。\n我目前記得的重點是：\n{bullet}\n\n如果有哪一點想更正或補充，你跟我說我就記起來。"
    if name and not uniq:
        return f"當然可以，{name}。\n我目前確定記得的是：你的名字是{name}。\n其他像興趣或生活習慣，我還想多了解一點點～你最近最常做、最喜歡做的事情是什麼呢？"
    # 沒名字
    return "當然可以～我目前對你還在慢慢認識中。\n我想先問一下：我可以怎麼稱呼你呢？你告訴我名字後，我之後每次都會用名字叫你。"

def respond(user_id: str, user_text: str, history: List[Dict[str, str]]) -> str:
    # 1) 先處理「吃藥已完成」
    if user_ack_med(user_text):
        mark_done(user_id)
        name = fetch_user_name(user_id)
        who = f"{name}" if name else "你"
        return f"太好了～謝謝{who}跟我說！那我今天就先不再提醒吃藥囉。"

    # 2) 如果使用者正在講名字，先存
    store_name_if_any(user_id, user_text)
    name = fetch_user_name(user_id)

    # 3) 使用者問「你對我的了解」
    if is_ask_profile(user_text):
        ans = summarize_user(user_id)
    else:
        # 4) 正常聊天：先撈記憶再回覆
        mem_ctx = build_memory_context(user_id, user_text, k=6)
        ans = call_llm(user_text, mem_ctx, history, name=name)

        # 若還沒有名字：自然補問一次（但不要每句都問）
        if not name and len(history) <= 2:
            ans += "\n\n我可以怎麼稱呼你呢？你告訴我名字後，我之後每次都會用名字叫你。"

    # 5) 5分鐘節點提醒（只把提醒接在回答後面，不要跳訊息）
    name = fetch_user_name(user_id)
    if should_remind_now(user_id):
        ans = ans.rstrip() + "\n\n" + reminder_text(name)

    # 6) 抽取長期記憶（不影響回覆）
    extract_and_store_memory(user_id, user_text)
    return ans
