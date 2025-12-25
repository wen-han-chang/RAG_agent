import os
import sqlite3
import time
from dataclasses import dataclass

DB_PATH = os.path.join(os.path.dirname(__file__), "state.db")

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
    CREATE TABLE IF NOT EXISTS med_state (
        user_id TEXT PRIMARY KEY,
        day_yyyymmdd TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0,
        last_slot TEXT NOT NULL DEFAULT ''
    )
    """)
    c.commit()

    # ✅ migration：如果舊表沒有 last_slot，就補上（避免你遇到 no such column）
    cols = [r[1] for r in c.execute("PRAGMA table_info(med_state)").fetchall()]
    if "last_slot" not in cols:
        c.execute("ALTER TABLE med_state ADD COLUMN last_slot TEXT NOT NULL DEFAULT ''")
        c.commit()

    return c

def _today_yyyymmdd() -> str:
    return time.strftime("%Y%m%d")

@dataclass
class MedState:
    user_id: str
    day_yyyymmdd: str
    done: bool
    last_slot: str  # e.g. 20251225-1050 (對齊5分鐘)

def get_med_state(user_id: str) -> MedState:
    today = _today_yyyymmdd()
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, day_yyyymmdd, done, last_slot FROM med_state WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO med_state(user_id, day_yyyymmdd, done, last_slot) VALUES (?, ?, 0, '')",
            (user_id, today)
        )
        conn.commit()
        conn.close()
        return MedState(user_id, today, False, "")

    uid, day, done, last_slot = row

    # 每天重置
    if day != today:
        cur.execute(
            "UPDATE med_state SET day_yyyymmdd=?, done=0, last_slot='' WHERE user_id=?",
            (today, user_id)
        )
        conn.commit()
        conn.close()
        return MedState(user_id, today, False, "")

    conn.close()
    return MedState(uid, day, bool(done), last_slot or "")

def mark_done(user_id: str):
    conn = _conn()
    conn.execute("UPDATE med_state SET done=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def update_last_slot(user_id: str, slot: str):
    conn = _conn()
    conn.execute("UPDATE med_state SET last_slot=? WHERE user_id=?", (slot, user_id))
    conn.commit()
    conn.close()
