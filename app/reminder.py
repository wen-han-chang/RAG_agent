import time
from datetime import datetime

from app.state_store import get_med_state, update_last_slot

ACK_KEYWORDS = ["我吃了", "吃過了", "已經吃了", "吃藥了", "我已吃", "ok 我吃了", "好了我吃了"]

def user_ack_med(text: str) -> bool:
    t = (text or "").strip()
    return any(k in t for k in ACK_KEYWORDS)

def _slot_now_5min() -> str:
    # 以系統時間對齊到 5 分鐘格：HHMM 會是 00,05,10,...55
    now = datetime.now()
    mm = (now.minute // 5) * 5
    slot = now.replace(minute=mm, second=0, microsecond=0)
    return slot.strftime("%Y%m%d-%H%M")

def should_remind_now(user_id: str) -> bool:
    """
    只有在「分鐘尾數 0 or 5」那一刻（minute%5==0）才提醒。
    而且同一個 slot 只提醒一次；使用者今天吃過了就不提醒。
    """
    st = get_med_state(user_id)
    if st.done:
        return False

    now = datetime.now()
    if now.minute % 5 != 0:
        return False

    slot = _slot_now_5min()
    if st.last_slot == slot:
        return False

    # ✅ 標記這個 slot 已提醒過
    update_last_slot(user_id, slot)
    return True

def reminder_text(name: str | None) -> str:
    who = f"{name}～" if name else "您～"
    return f"對了 {who}溫馨提醒一下：差不多該吃藥了。吃完跟我說「我吃了」，我今天就不再提醒您囉。"
