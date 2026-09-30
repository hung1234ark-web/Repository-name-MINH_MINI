import json
from pathlib import Path
import requests


# ==================================================
# MINH MINI - MEMORY V2
# ==================================================

BASE_DIR = Path.home() / "MINH_MINI"
CONFIG_FILE = BASE_DIR / "config" / "config.json"
MEMORY_FILE = BASE_DIR / "memory" / "memory.json"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remember(memory, text):
    text = text.strip()

    if not text:
        return "Lam chưa nói điều gì để Minh ghi nhớ."

    if "memories" not in memory:
        memory["memories"] = []

    if text not in memory["memories"]:
        memory["memories"].append(text)
        save_json(MEMORY_FILE, memory)
        return f"Minh nhớ rồi nha: {text}"

    return "Điều này Minh đã nhớ rồi nè."


def show_memories(memory):
    memories = memory.get("memories", [])

    if not memories:
        return "Hiện tại Minh chưa có ký ức riêng nào được Lam lưu."

    result = "Những điều Minh đang nhớ:\n"

    for i, item in enumerate(memories, 1):
        result += f"{i}. {item}\n"

    return result.strip()


def clear_memories(memory):
    memory["memories"] = []
    save_json(MEMORY_FILE, memory)

    return "Minh đã xóa các ký ức Lam yêu cầu rồi."


def handle_memory_command(message, memory):
    text = message.strip()
    lower = text.lower()

    # Lệnh nhớ
    if lower.startswith("nhớ rằng "):
        content = text[9:].strip()
        return remember(memory, content)

    if lower.startswith("nhớ "):
        content = text[4:].strip()

        if content:
            return remember(memory, content)

    # Xem bộ nhớ
    if lower in (
        "tôi nhớ gì",
        "tôi đã nói gì",
        "xem bộ nhớ",
        "xem ký ức",
        "minh nhớ gì",
        "bộ nhớ"
    ):
        return show_memories(memory)

    # Xóa bộ nhớ
    if lower in (
        "xóa ký ức",
        "xóa bộ nhớ",
        "xóa tất cả ký ức"
    ):
        return clear_memories(memory)

    return None


def ask_minh(message, config, memory, history):

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    memories = memory.get("memories", [])

    if memories:
        memory_text = "\n".join(
            f"- {item}" for item in memories
        )
    else:
        memory_text = "- Chưa có ký ức bổ sung."

    system_prompt = f"""
Bạn là {assistant_name}, trợ lý riêng của {user_name}.

THÔNG TIN CỐ ĐỊNH:
- Tên người dùng: {user_name}
- Tên trợ lý: {assistant_name}

KÝ ỨC ĐÃ ĐƯỢC LƯU:
{memory_text}

QUY TẮC:
1. Gọi người dùng là {user_name} khi phù hợp.
2. Nếu được hỏi "bạn tên gì", trả lời rằng bạn là {assistant_name}.
3. Nếu được hỏi "tôi tên gì", trả lời rằng người dùng tên {user_name}.
4. Sử dụng các ký ức đã lưu khi chúng liên quan đến câu hỏi.
5. Không được tự bịa ra ký ức chưa được lưu.
6. Nếu người dùng nói tiếng Việt, trả lời bằng tiếng Việt.
7. Nói chuyện tự nhiên, thân thiện.
8. Câu hỏi đơn giản thì trả lời ngắn gọn.
9. Nếu không biết, nói rõ là không biết.
10. Không tự nhận mình có quyền điều khiển máy tính hoặc Internet
    nếu MINH MINI chưa được cấp công cụ tương ứng.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": message
    })

    url = config["ollama_url"].rstrip("/") + "/api/chat"

    payload = {
        "model": config["model"],
        "messages": messages,
        "stream": False
    }

    response = requests.post(
        url,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    answer = data["message"]["content"].strip()

    return answer


def main():

    config = load_json(CONFIG_FILE)
    memory = load_json(MEMORY_FILE)

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    history = []

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

            # Thoát
            if message.lower() in (
                "thoat",
                "exit",
                "quit"
            ):
                print(
                    f"{assistant_name} tạm biệt {user_name}!"
                )
                break

            # Xử lý bộ nhớ
            memory_result = handle_memory_command(
                message,
                memory
            )

            if memory_result is not None:

                print(
                    f"{assistant_name} > "
                    f"{memory_result}"
                )
                print()

                continue

            # Chat với Minh
            answer = ask_minh(
                message,
                config,
                memory,
                history
            )

            print(
                f"{assistant_name} > {answer}"
            )
            print()

            # Lưu lịch sử phiên hiện tại
            history.append({
                "role": "user",
                "content": message
            })

            history.append({
                "role": "assistant",
                "content": answer
            })

            # Chỉ giữ 20 tin nhắn gần nhất
            if len(history) > 20:
                history = history[-20:]

        except KeyboardInterrupt:

            print(
                f"\n{assistant_name} đã dừng an toàn."
            )
            break

        except requests.exceptions.ConnectionError:

            print(
                f"{assistant_name} > "
                "Không kết nối được với Ollama."
            )
            print()

        except requests.exceptions.Timeout:

            print(
                f"{assistant_name} > "
                "Ollama phản hồi quá lâu."
            )
            print()

        except Exception as e:

            print(
                f"{assistant_name} > Có lỗi: {e}"
            )
            print()


if __name__ == "__main__":
    main()