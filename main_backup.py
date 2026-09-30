import json
import requests
from pathlib import Path

BASE_DIR = Path.home() / "MINH_MINI"
CONFIG_FILE = BASE_DIR / "config" / "config.json"
MEMORY_FILE = BASE_DIR / "memory" / "memory.json"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def ask_minh(message, config, memory):
    url = config["ollama_url"] + "/api/chat"

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    system_prompt = f"""
Bạn là {assistant_name}, trợ lý riêng của {user_name}.

Thông tin cố định:
- Tên người dùng: {user_name}
- Tên trợ lý: {assistant_name}

Hãy luôn gọi người dùng là {user_name}.
Khi được hỏi "bạn tên gì", trả lời rằng bạn là {assistant_name}.
Khi được hỏi "tôi tên gì", trả lời rằng người dùng tên {user_name}.
Trả lời tự nhiên, thân thiện và ngắn gọn khi câu hỏi đơn giản.
"""

    data = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False
    }

    response = requests.post(url, json=data, timeout=300)
    response.raise_for_status()

    return response.json()["message"]["content"]


def main():
    config = load_json(CONFIG_FILE)
    memory = load_json(MEMORY_FILE)

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    print("=" * 50)
    print(f"        {assistant_name}")
    print("=" * 50)
    print(f"Xin chào {user_name}!")
    print(f"{assistant_name} đã khởi động.")
    print("Gõ 'thoat' để đóng.")
    print()

    while True:
        try:
            message = input(f"{user_name} > ").strip()

            if not message:
                continue

            if message.lower() in ("thoat", "exit", "quit"):
                print(f"{assistant_name} tạm biệt {user_name}!")
                break

            answer = ask_minh(message, config, memory)
            print(f"{assistant_name} > {answer}")
            print()

        except KeyboardInterrupt:
            print(f"\n{assistant_name} đã dừng an toàn.")
            break

        except Exception as e:
            print(f"{assistant_name} > Có lỗi: {e}")
            print()


if __name__ == "__main__":
    main()
