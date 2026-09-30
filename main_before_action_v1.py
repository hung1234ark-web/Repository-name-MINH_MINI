import json
from pathlib import Path
import requests
import re
import unicodedata

from web import safe_search
from web_ai import summarize_results


BASE_DIR = Path.home() / "MINH_MINI"
CONFIG_FILE = BASE_DIR / "config" / "config.json"
MEMORY_FILE = BASE_DIR / "memory" / "memory.json"


# =========================================================
# JSON
# =========================================================

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================================================
# TYPO V4.0
# =========================================================

COMMON_TYPOS = {
    # Giá
    "gí": "giá",
    "gía": "giá",
    "giaa": "giá",

    # iPhone
    "iphon": "iphone",
    "ipone": "iphone",
    "iphonee": "iphone",

    # Sầu riêng
    "sau rieng": "sầu riêng",
    "saurieng": "sầu riêng",
    "sầu riềng": "sầu riêng",

    # Măng cụt
    "măng cut": "măng cụt",
    "mang cut": "măng cụt",
    "mang cutt": "măng cụt",
    "mangcut": "măng cụt",

    # Memory / lệnh
    "sóa": "xóa",
    "sóa": "xóa",
    "xoa": "xóa",

    "quên răng": "quên rằng",
    "quen rang": "quên rằng",

    "kiêm tra": "kiểm tra",
    "kiem tra": "kiểm tra",

    "kiêm tra bộ nhớ": "kiểm tra bộ nhớ",
    "kiêm tra bo nho": "kiểm tra bộ nhớ",

    # Không dấu
    "bao nhieu": "bao nhiêu",
    "hien tai": "hiện tại",
    "hom nay": "hôm nay",
    "moi nhat": "mới nhất",
}


def normalize_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


def normalize_typo(text):
    original = text

    text = normalize_spaces(text)
    text = unicodedata.normalize("NFC", text)

    normalized = text

    typo_list = sorted(
        COMMON_TYPOS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for wrong, correct in typo_list:
        pattern = r"(?<!\w)" + re.escape(wrong) + r"(?!\w)"

        normalized = re.sub(
            pattern,
            correct,
            normalized,
            flags=re.IGNORECASE
        )

    return normalized if normalized.lower() != original.lower() else original


# =========================================================
# TEXT KEY
# Dùng để so khớp ký ức khi Lam gõ sai dấu nhẹ.
# Ví dụ:
# ègg -> egg
# ẻgg -> egg
# =========================================================

def memory_key(text):
    text = text.strip().lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = unicodedata.normalize(
        "NFC",
        text
    )

    text = normalize_spaces(text)

    return text


# =========================================================
# MEMORY
# =========================================================

def remember(memory, text):
    text = text.strip()

    if not text:
        return "Lam chưa nói điều Minh cần nhớ."

    if "memories" not in memory:
        memory["memories"] = []

    # Không lưu trùng kể cả khi khác hoa/thường hoặc dấu nhẹ
    new_key = memory_key(text)

    for item in memory["memories"]:
        if memory_key(item) == new_key:
            return "Minh đã nhớ điều này rồi."

    memory["memories"].append(text)

    save_json(
        MEMORY_FILE,
        memory
    )

    return f"Minh nhớ rồi nha: {text}"


def show_memories(memory):
    memories = memory.get("memories", [])

    if not memories:
        return "Hiện tại Minh chưa lưu ký ức nào."

    lines = [
        "Những điều Minh đang nhớ:"
    ]

    for i, item in enumerate(memories, 1):
        lines.append(
            f"{i}. {item}"
        )

    return "\n".join(lines)


def clear_memories(memory):
    memory["memories"] = []

    save_json(
        MEMORY_FILE,
        memory
    )

    return "Minh đã xóa các ký ức đã lưu."


def forget_memory(memory, text):
    text = text.strip()

    if not text:
        return "Lam chưa nói điều Minh cần quên."

    memories = memory.get(
        "memories",
        []
    )

    target_key = memory_key(text)

    for i, item in enumerate(memories):

        # So khớp chính xác sau khi bỏ khác biệt hoa/thường
        # và dấu tiếng Việt
        if memory_key(item) == target_key:

            removed_item = memories.pop(i)

            save_json(
                MEMORY_FILE,
                memory
            )

            return (
                f"Minh đã quên: "
                f"{removed_item}"
            )

    return (
        f"Minh không tìm thấy ký ức: "
        f"{text}"
    )


# =========================================================
# MEMORY COMMAND ROUTER V4.0
# =========================================================

def handle_memory_command(message, memory):
    """
    Bộ định tuyến Memory.

    Memory được xử lý trước AI.

    AI không được tự quyết định:
    - nhớ
    - lưu
    - quên
    - xóa
    - xem bộ nhớ
    """

    text = normalize_typo(message)
    lower = text.lower().strip()

    # =====================================================
    # NHỚ / LƯU / GHI NHỚ
    # =====================================================

    memory_prefixes = (
        "nhớ rằng ",
        "nhớ ",
        "lưu ",
        "ghi nhớ "
    )

    for prefix in memory_prefixes:

        if lower.startswith(prefix):

            content = text[len(prefix):].strip()

            if content:
                return True, remember(
                    memory,
                    content
                )

            return True, (
                "Lam chưa nói điều "
                "Minh cần nhớ."
            )

    # =====================================================
    # XEM / KIỂM TRA BỘ NHỚ
    # =====================================================

    memory_view_commands = (
        "tôi nhớ gì",
        "toi nho gi",

        "xem bộ nhớ",
        "xem bo nho",

        "kiểm tra bộ nhớ",
        "kiem tra bo nho",

        "cho xem bộ nhớ",
        "cho xem bo nho",

        "bộ nhớ của minh",
        "bo nho cua minh",

        "kiểm tra dữ liệu",
        "kiem tra du lieu",

        "xem dữ liệu",
        "xem du lieu",

        "minh nhớ gì",
        "minh nho gi"
    )

    if lower in memory_view_commands:

        return True, show_memories(
            memory
        )

    # =====================================================
    # QUÊN MỘT KÝ ỨC
    # =====================================================

    if lower.startswith(
        "quên rằng "
    ):

        content = text[
            len("quên rằng "):
        ].strip()

        return True, forget_memory(
            memory,
            content
        )

    if lower.startswith(
        "quên "
    ):

        content = text[
            len("quên "):
        ].strip()

        return True, forget_memory(
            memory,
            content
        )

    # =====================================================
    # XÓA MỘT KÝ ỨC
    #
    # Ví dụ:
    # xóa ègg
    # sóa ègg
    # xoa ègg
    # =====================================================

    delete_prefixes = (
        "xóa ",
        "xoa ",
        "sóa "
    )

    for prefix in delete_prefixes:

        if lower.startswith(prefix):

            content = text[
                len(prefix):
            ].strip()

            if not content:
                return True, (
                    "Lam chưa nói điều "
                    "Minh cần xóa."
                )

            return True, forget_memory(
                memory,
                content
            )

    # =====================================================
    # XÓA TOÀN BỘ BỘ NHỚ
    # =====================================================

    clear_commands = (
        "xóa ký ức",
        "xoa ky uc",

        "xóa bộ nhớ",
        "xoa bo nho",

        "xóa tất cả ký ức",
        "xoa tat ca ky uc",

        "xóa hết ký ức",
        "xoa het ky uc"
    )

    if lower in clear_commands:

        return True, clear_memories(
            memory
        )

    return False, None


# =========================================================
# WEB QUERY
# =========================================================

def extract_web_query(message):
    text = normalize_typo(message)
    lower = text.lower()

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

            return text[
                len(prefix):
            ].strip()

    web_keywords = (
        "giá",
        "bao nhiêu",
        "hiện tại",
        "hôm nay",
        "mới nhất",
        "mới",
        "tin tức",
        "tin mới",
        "thời tiết",
        "địa chỉ",
        "website",
        "trang chủ",
        "sản phẩm",
        "mua ở đâu",
        "ở đâu",
        "tìm",
        "kiếm",
        "review",
        "đánh giá",
        "so sánh",
        "lịch",
        "giờ",
        "2026"
    )

    question_patterns = (
        "có giá",
        "giá bao nhiêu",
        "giá bao nhiêu vậy",
        "mua ở đâu",
        "tìm ở đâu",
        "ở đâu bán",
        "thông tin mới nhất",
        "hôm nay có gì",
        "hiện nay",
        "bây giờ"
    )

    if any(
        keyword in lower
        for keyword in web_keywords
    ):
        return text

    if any(
        pattern in lower
        for pattern in question_patterns
    ):
        return text

    return None


# =========================================================
# CHAT
# =========================================================

def ask_minh(
    message,
    config,
    memory,
    history
):

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    memories = memory.get(
        "memories",
        []
    )

    if memories:

        memory_text = "\n".join(
            f"- {item}"
            for item in memories
        )

    else:

        memory_text = (
            "- Chưa có ký ức bổ sung."
        )

    system_prompt = f"""
Bạn là {assistant_name}, trợ lý riêng của {user_name}.

THÔNG TIN:
- Tên người dùng: {user_name}
- Tên trợ lý: {assistant_name}

KÝ ỨC:
{memory_text}

QUY TẮC:

1. Gọi người dùng là {user_name} khi phù hợp.
2. Nếu được hỏi tên, trả lời đúng theo thông tin trên.
3. Trả lời bằng tiếng Việt nếu người dùng nói tiếng Việt.
4. Câu hỏi đơn giản thì trả lời ngắn gọn.
5. Không tự nhận có quyền điều khiển máy tính hoặc Internet
   nếu chưa được cấp công cụ.
6. Không bịa thông tin.
7. Nói chuyện tự nhiên, thân thiện.
8. Không tự ý thêm, xóa hoặc thay đổi ký ức.
9. Các lệnh nhớ, quên, xóa, lưu, xem bộ nhớ
   đã được chương trình xử lý trước khi gọi AI.
10. Không được nói "đã nhớ", "đã lưu", "đã xóa"
    hoặc "đã quên" nếu chương trình chưa thực hiện hành động đó.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(
        history
    )

    messages.append({
        "role": "user",
        "content": message
    })

    url = (
        config["ollama_url"].rstrip("/")
        + "/api/chat"
    )

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

    return data[
        "message"
    ][
        "content"
    ].strip()


# =========================================================
# MAIN
# =========================================================

def main():

    config = load_json(
        CONFIG_FILE
    )

    memory = load_json(
        MEMORY_FILE
    )

    user_name = memory[
        "user"
    ][
        "name"
    ]

    assistant_name = memory[
        "assistant"
    ][
        "name"
    ]

    history = []

    print("=" * 50)
    print(
        f"        {assistant_name}"
    )
    print("=" * 50)

    print(
        f"Xin chào {user_name}!"
    )

    print(
        f"{assistant_name} đã khởi động."
    )

    print(
        "Gõ 'thoat' để đóng."
    )

    print()

    while True:

        try:

            message = input(
                f"{user_name} > "
            ).strip()

            if not message:
                continue

            # =================================================
            # THOÁT
            # =================================================

            if message.lower() in (
                "thoat",
                "thoát",
                "exit",
                "quit"
            ):

                print(
                    f"{assistant_name} "
                    f"tạm biệt {user_name}!"
                )

                break

            # =================================================
            # NORMALIZE TYPO
            # =================================================

            normalized_message = (
                normalize_typo(message)
            )

            # =================================================
            # MEMORY
            # =================================================

            handled, result = (
                handle_memory_command(
                    normalized_message,
                    memory
                )
            )

            if handled:

                print(
                    f"{assistant_name} > "
                    f"{result}"
                )

                print()

                continue

            # =================================================
            # WEB
            # =================================================

            query = extract_web_query(
                normalized_message
            )

            if query:

                if (
                    query.lower()
                    != message.lower()
                ):

                    print(
                        f"{assistant_name} > "
                        f"Minh hiểu câu hỏi là: "
                        f"{query}"
                    )

                print(
                    f"{assistant_name} > "
                    "Đang kiểm tra thông tin "
                    "trên web..."
                )

                try:

                    results = safe_search(
                        query,
                        max_results=5
                    )

                    if not results:

                        print(
                            f"{assistant_name} > "
                            "Minh không tìm thấy "
                            "kết quả phù hợp."
                        )

                        print()

                        continue

                    answer = summarize_results(
                        query,
                        results,
                        config,
                        memory
                    )

                    print(
                        f"{assistant_name} > "
                        f"{answer}"
                    )

                    print()

                except requests.exceptions.RequestException:

                    print(
                        f"{assistant_name} > "
                        "Minh không kết nối "
                        "được với web."
                    )

                    print()

                except Exception as e:

                    print(
                        f"{assistant_name} > "
                        f"Lỗi Web: {e}"
                    )

                    print()

                continue

            # =================================================
            # CHAT BÌNH THƯỜNG
            # =================================================

            chat_message = (
                normalized_message
            )

            answer = ask_minh(
                chat_message,
                config,
                memory,
                history
            )

            print(
                f"{assistant_name} > "
                f"{answer}"
            )

            print()

            history.append({
                "role": "user",
                "content": chat_message
            })

            history.append({
                "role": "assistant",
                "content": answer
            })

            if len(history) > 20:

                history = history[
                    -20:
                ]

        except KeyboardInterrupt:

            print(
                f"\n{assistant_name} "
                "đã dừng an toàn."
            )

            break

        except requests.exceptions.ConnectionError:

            print(
                f"{assistant_name} > "
                "Không kết nối được với "
                "Ollama. Hãy kiểm tra "
                "Ollama đang chạy."
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
                f"{assistant_name} > "
                f"Có lỗi: {e}"
            )

            print()


if __name__ == "__main__":
    main()