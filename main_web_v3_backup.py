import json
from pathlib import Path
import requests

from web import safe_search
from web_ai import summarize_results


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
        return "Lam chưa nói điều Minh cần nhớ."

    if "memories" not in memory:
        memory["memories"] = []

    if text not in memory["memories"]:
        memory["memories"].append(text)
        save_json(MEMORY_FILE, memory)
        return f"Minh nhớ rồi nha: {text}"

    return "Minh đã nhớ điều này rồi."


def show_memories(memory):
    memories = memory.get("memories", [])

    if not memories:
        return "Hiện tại Minh chưa lưu ký ức nào."

    lines = ["Những điều Minh đang nhớ:"]

    for i, item in enumerate(memories, 1):
        lines.append(f"{i}. {item}")

    return "\n".join(lines)


def clear_memories(memory):
    memory["memories"] = []
    save_json(MEMORY_FILE, memory)
    return "Minh đã xóa các ký ức đã lưu."


def handle_memory_command(message, memory):
    text = message.strip()
    lower = text.lower()

    if lower.startswith("nhớ rằng "):
        content = text[9:].strip()
        return True, remember(memory, content)

    if lower.startswith("nhớ "):
        content = text[4:].strip()
        return True, remember(memory, content)

    if lower in ("tôi nhớ gì", "toi nho gi", "xem bộ nhớ", "xem bo nho"):
        return True, show_memories(memory)

    if lower in ("xóa ký ức", "xoa ky uc", "xóa bộ nhớ", "xoa bo nho"):
        return True, clear_memories(memory)

    return False, None


def is_web_command(message):
    lower = message.lower().strip()

    prefixes = (
        "tìm trên web ",
        "tim tren web ",
        "tìm web ",
        "tim web ",
        "search web ",
        "search "
    )

    for prefix in prefixes:
        if lower.startswith(prefix):
            return True, message[len(prefix):].strip()

    return False, None


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

KÝ ỨC ĐÃ LƯU:
{memory_text}

QUY TẮC:
1. Gọi người dùng là {user_name} khi phù hợp.
2. Nếu được hỏi "bạn tên gì", trả lời rằng bạn là {assistant_name}.
3. Nếu được hỏi "tôi tên gì", trả lời rằng người dùng tên {user_name}.
4. Trả lời bằng tiếng Việt nếu người dùng nói tiếng Việt.
5. Câu hỏi đơn giản thì trả lời ngắn gọn.
6. Có thể dùng các ký ức đã lưu để hiểu ngữ cảnh.
7. Không tự nhận mình có quyền điều khiển máy tính hoặc Internet
   nếu chưa được cấp công cụ tương ứng.
8. Nếu không biết, nói rõ là không biết thay vì bịa.
"""

    messages = [
        {"role": "system", "content": system_prompt}
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

    return data["message"]["content"].strip()


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

            if message.lower() in ("thoat", "exit", "quit"):
                print(f"{assistant_name} tạm biệt {user_name}!")
                break

            # =========================
            # MEMORY
            # =========================

            handled, result = handle_memory_command(
                message,
                memory
            )

            if handled:
                print(f"{assistant_name} > {result}")
                print()
                continue

            # =========================
            # WEB + AI
            # =========================

            is_web, query = is_web_command(message)

            if is_web:
                if not query:
                    print(
                        f"{assistant_name} > "
                        "Lam cần nói điều muốn tìm nhé."
                    )
                    print()
                    continue

                print(
                    f"{assistant_name} > "
                    f"Đang tìm trên web: {query}"
                )

                try:
                    results = safe_search(
                        query,
                        max_results=5
                    )

                    if not results:
                        print(
                            f"{assistant_name} > "
                            "Minh không tìm thấy kết quả phù hợp."
                        )
                        print()
                        continue

                    answer = summarize_results(
                        query,
                        results,
                        config,
                        memory
                    )

                    print(f"{assistant_name} > {answer}")
                    print()

                except requests.exceptions.RequestException:
                    print(
                        f"{assistant_name} > "
                        "Minh không kết nối được với web."
                    )
                    print()

                except Exception as e:
                    print(
                        f"{assistant_name} > "
                        f"Lỗi Web: {e}"
                    )
                    print()

                continue

            # =========================
            # CHAT
            # =========================

            answer = ask_minh(
                message,
                config,
                memory,
                history
            )

            print(f"{assistant_name} > {answer}")
            print()

            history.append({
                "role": "user",
                "content": message
            })

            history.append({
                "role": "assistant",
                "content": answer
            })

            if len(history) > 20:
                history = history[-20:]

        except KeyboardInterrupt:
            print(f"\n{assistant_name} đã dừng an toàn.")
            break

        except requests.exceptions.ConnectionError:
            print(
                f"{assistant_name} > "
                "Không kết nối được với Ollama. "
                "Hãy kiểm tra Ollama đang chạy."
            )
            print()

        except requests.exceptions.Timeout:
            print(
                f"{assistant_name} > "
                "Ollama phản hồi quá lâu. "
                "Lam thử lại câu ngắn hơn nhé."
            )
            print()

        except Exception as e:
            print(f"{assistant_name} > Có lỗi: {e}")
            print()


if __name__ == "__main__":
    main()