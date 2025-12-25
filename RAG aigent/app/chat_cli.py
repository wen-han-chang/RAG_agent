from typing import List, Dict
from app.agent import respond

def chat_loop(user_id: str = "willy"):
    print("✅ Chat CLI started. 輸入 /exit 結束")

    history: List[Dict[str, str]] = []

    while True:
        try:
            user_text = input("你：").strip()
        except KeyboardInterrupt:
            print("\n👋 已結束。")
            break

        if not user_text:
            continue
        if user_text == "/exit":
            print("👋 已結束。")
            break

        ans = respond(user_id=user_id, user_text=user_text, history=history)
        print(f"\n助理：{ans}\n")

        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": ans})

if __name__ == "__main__":
    chat_loop("willy")
