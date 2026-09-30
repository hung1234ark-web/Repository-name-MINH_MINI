
import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime

from action import handle_action_command
from web import safe_search
from web_ai import summarize_results


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path.home() / "MINH_MINI"
MEMORY_FILE = BASE_DIR / "memory" / "memory.json"
CONFIG_FILE = BASE_DIR / "config" / "config.json"


# ============================================================
# MEMORY V4.0
# ============================================================

def load_memory():
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            "[]",
            encoding="utf-8"
        )

    try:
        data = json.loads(
            MEMORY_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


def save_memory(memory):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    MEMORY_FILE.write_text(
        json.dumps(
            memory,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


memory = load_memory()


def memory_key(text):
    text = str(text).strip().lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    return " ".join(text.split())


def remember(text):
    global memory

    text = text.strip()

    if not text:
        return False

    key = memory_key(text)

    for item in memory:
        if memory_key(item) == key:
            return False

    memory.append(text)
    save_memory(memory)

    return True


def forget_memory(text):
    global memory

    text = text.strip()

    if not text:
        return None

    key = memory_key(text)

    for item in memory[:]:
        if memory_key(item) == key:
            memory.remove(item)
            save_memory(memory)
            return item

    return None


def clear_memory():
    global memory

    memory = []
    save_memory(memory)


def handle_memory_command(message):
    text = message.strip()
    normalized = memory_key(text)

    # -------------------------
    # XEM BỘ NHỚ
    # -------------------------

    view_commands = (
        "xem bo nho",
        "kiem tra bo nho",
        "kiem tra du lieu",
        "xem du lieu",
        "xem memory",
        "show memory",
    )

    if normalized in view_commands:

        if not memory:
            return True, "Hiện tại Minh chưa nhớ điều gì."

        lines = [
            "Những điều Minh đang nhớ:"
        ]

        for index, item in enumerate(memory, 1):
            lines.append(
                f"{index}. {item}"
            )

        return True, "\n".join(lines)

    # -------------------------
    # XÓA TOÀN BỘ
    # -------------------------

    clear_commands = (
        "xoa tat ca bo nho",
        "xoa het bo nho",
        "xoa bo nho",
        "xoa tat ca du lieu",
        "xoa het du lieu",
        "clear memory",
    )

    if normalized in clear_commands:

        clear_memory()

        return True, "Minh đã xóa toàn bộ bộ nhớ."

    # -------------------------
    # NHỚ
    # -------------------------

    remember_prefixes = (
        "nhớ ",
        "nho ",
        "lưu ",
        "luu ",
        "ghi nhớ ",
        "ghi nho ",
    )

    for prefix in remember_prefixes:

        if text.lower().startswith(prefix.lower()):

            content = text[len(prefix):].strip()

            if not content:
                return True, "Lam muốn Minh nhớ điều gì?"

            if remember(content):
                return True, f"Minh nhớ rồi nha: {content}"

            return True, "Điều này Minh đã nhớ rồi."

    # -------------------------
    # QUÊN / XÓA
    # -------------------------

    forget_prefixes = (
        "quên rằng ",
        "quen rang ",
        "quên ",
        "quen ",
        "xóa ",
        "xoa ",
        "sóa ",
        "soa ",
    )

    for prefix in forget_prefixes:

        if text.lower().startswith(prefix.lower()):

            content = text[len(prefix):].strip()

            if not content:
                return True, "Lam muốn Minh quên điều gì?"

            deleted = forget_memory(content)

            if deleted is not None:
                return True, f"Minh đã quên: {deleted}"

            return True, "Minh không tìm thấy điều đó trong bộ nhớ."

    return False, None


# ============================================================
# TYPO SYSTEM
# ============================================================

COMMON_TYPOS = {
    "gí": "giá",
    "gía": "giá",
    "giaa": "giá",

    "iphon": "iphone",
    "ipone": "iphone",
    "iphonee": "iphone",

    "sau rieng": "sầu riêng",
    "saurieng": "sầu riêng",
    "sầu riềng": "sầu riêng",

    "măng cut": "măng cụt",
    "mang cut": "măng cụt",
    "mang cutt": "măng cụt",
    "mangcut": "măng cụt",

    "bao nhieu": "bao nhiêu",
    "hien tai": "hiện tại",
    "hom nay": "hôm nay",
    "moi nhat": "mới nhất",
}


def normalize_spaces(text):
    return " ".join(text.split())


def normalize_typo(text):
    result = text

    for wrong, correct in COMMON_TYPOS.items():
        pattern = re.compile(
            re.escape(wrong),
            re.IGNORECASE
        )

        result = pattern.sub(
            correct,
            result
        )

    return normalize_spaces(result)


# ============================================================
# TIME / DATE
# ============================================================

def get_current_time():
    now = datetime.now()

    return (
        f"Bây giờ là "
        f"{now.strftime('%H:%M:%S')}."
    )


def get_current_date():
    now = datetime.now()

    weekdays = {
        0: "thứ Hai",
        1: "thứ Ba",
        2: "thứ Tư",
        3: "thứ Năm",
        4: "thứ Sáu",
        5: "thứ Bảy",
        6: "Chủ nhật",
    }

    return (
        f"Hôm nay là "
        f"{weekdays[now.weekday()]}, "
        f"ngày {now.strftime('%d/%m/%Y')}."
    )


def handle_time_date(message):
    text = memory_key(message)

    time_patterns = (
        "may gio",
        "bay gio la may gio",
        "bay gio may gio",
        "gio hien tai",
        "hien tai may gio",
        "may gio roi",
    )

    date_patterns = (
        "hom nay ngay may",
        "hom nay la ngay may",
        "hom nay thu may",
        "hom nay la thu may",
        "ngay hom nay",
    )

    for pattern in time_patterns:
        if pattern in text:
            return True, get_current_time()

    for pattern in date_patterns:
        if pattern in text:
            return True, get_current_date()

    return False, None


# ============================================================
# ACTION ROUTER
# ============================================================

def extract_youtube_search(message):
    text = normalize_typo(message)

    patterns = [
        r"(?:mở|mo)\s+(?:ytb|youtube)\s+(?:và\s+)?(?:tìm|tim|tìm kiếm|tim kiem)\s+(.+)",
        r"(?:mở|mo)\s+(?:ytb|youtube)\s+(.+?)\s+(?:trong|tren)\s+youtube",
        r"(?:tìm|tim|tìm kiếm|tim kiem)\s+(.+?)\s+(?:trên|tren)\s+youtube",
        r"(?:youtube|ytb)\s+(?:tìm|tim|tìm kiếm|tim kiem)\s+(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            query = match.group(1).strip()

            if query:
                return query

    return None


def open_facebook():
    import webbrowser

    webbrowser.open(
        "https://www.facebook.com"
    )

    return "Minh đã mở Facebook."


def open_youtube_search(query):
    import webbrowser
    from urllib.parse import quote_plus

    url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )

    webbrowser.open(url)

    return (
        f"Minh đã mở YouTube và tìm "
        f"“{query}”."
    )


def handle_custom_actions(message):

    normalized = memory_key(
        normalize_typo(message)
    )

    # --------------------------------
    # TIME / DATE
    # --------------------------------

    handled, result = handle_time_date(
        message
    )

    if handled:
        return True, result

    # --------------------------------
    # YOUTUBE SEARCH
    # --------------------------------

    youtube_query = extract_youtube_search(
        message
    )

    if youtube_query:

        return True, open_youtube_search(
            youtube_query
        )

    # --------------------------------
    # FACEBOOK
    # --------------------------------

    facebook_patterns = (
        "mo facebook",
        "mo fb",
        "truy cap facebook",
        "truy cap fb",
        "vao facebook",
        "vao fb",
    )

    if normalized in facebook_patterns:
        return True, open_facebook()

    # --------------------------------
    # ACTION.PY
    # --------------------------------

    handled, result = handle_action_command(
        normalize_typo(message)
    )

    if handled:
        return True, result

    return False, None


# ============================================================
# WEB QUERY
# ============================================================

WEB_KEYWORDS = (
    "giá",
    "gia",
    "mới nhất",
    "moi nhat",
    "hiện tại",
    "hien tai",
    "tin tức",
    "tin tuc",
    "hôm nay",
    "hom nay",
    "thời tiết",
    "thoi tiet",
    "tìm kiếm",
    "tim kiem",
    "tra cứu",
    "tra cuu",
)


def extract_web_query(message):

    normalized = normalize_typo(
        message
    )

    # Không cho câu hỏi ngày/giờ
    # chạy sang Web.
    handled, _ = handle_time_date(
        normalized
    )

    if handled:
        return None

    text = normalized.strip()

    if not text:
        return None

    text_key = memory_key(text)

    for keyword in WEB_KEYWORDS:

        if memory_key(keyword) in text_key:
            return text

    return None


# ============================================================
# OLLAMA CHAT
# ============================================================

def load_config():

    if not CONFIG_FILE.exists():
        return {}

    try:
        return json.loads(
            CONFIG_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {}


def ask_minh(message):

    config = load_config()

    model = config.get(
        "model",
        "qwen3:1.7b"
    )

    url = config.get(
        "url",
        "http://localhost:11434"
    )

    try:
        import requests

        endpoint = url.rstrip("/")

        if not endpoint.endswith("/api/chat"):
            endpoint += "/api/chat"

        prompt = f"""
Lam đang nói chuyện với Minh Mini.

Quy tắc:
- Gọi người dùng là Lam.
- Minh tự xưng là Minh.
- Không tự xưng là "tôi".
- Không gọi Lam là "bạn".
- Trả lời bằng tiếng Việt tự nhiên.
- Nếu Lam yêu cầu một hành động mà chương trình chưa thực hiện,
  không được nói rằng hành động đã được thực hiện.
- Không bịa thông tin.
- Trả lời ngắn gọn với câu hỏi đơn giản.

Tin nhắn của Lam:
{message}
"""

        response = requests.post(
            endpoint,
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return (
            data.get("message", {})
            .get("content", "")
            .strip()
        )

    except Exception as error:

        return (
            "Minh chưa thể kết nối bộ não AI "
            f"lúc này. Lỗi: {error}"
        )


# ============================================================
# WEB AI
# ============================================================

def handle_web_request(query):

    print(
        "Minh Mini > "
        "Đang kiểm tra thông tin trên web..."
    )

    try:
        results = safe_search(
            query,
            max_results=5
        )

        if not results:
            return (
                "Minh không tìm thấy kết quả phù hợp."
            )

        answer = summarize_results(
            query,
            results
        )

        return answer

    except Exception as error:

        return (
            "Minh gặp lỗi khi kiểm tra web: "
            f"{error}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 50)
    print("        Minh Mini")
    print("=" * 50)
    print("Xin chào Lam!")
    print("Minh Mini đã khởi động.")
    print("Gõ 'thoat' để đóng.")
    print()

    while True:

        try:
            message = input("Lam > ").strip()

        except KeyboardInterrupt:
            print()
            print("Minh Mini tạm biệt Lam!")
            break

        except EOFError:
            print()
            print("Minh Mini tạm biệt Lam!")
            break

        if not message:
            continue

        # --------------------------------
        # EXIT
        # --------------------------------

        if message.lower().strip() in (
            "thoat",
            "thoát",
            "exit",
            "quit",
        ):

            print(
                "Minh Mini tạm biệt Lam!"
            )

            break

        # --------------------------------
        # NORMALIZE TYPO
        # --------------------------------

        message = normalize_typo(
            message
        )

        # --------------------------------
        # MEMORY
        # --------------------------------

        handled, result = (
            handle_memory_command(
                message
            )
        )

        if handled:

            print(
                f"Minh Mini > {result}"
            )

            continue

        # --------------------------------
        # CUSTOM ACTIONS
        # --------------------------------

        handled, result = (
            handle_custom_actions(
                message
            )
        )

        if handled:

            print(
                f"Minh Mini > {result}"
            )

            continue

        # --------------------------------
        # WEB
        # --------------------------------

        web_query = extract_web_query(
            message
        )

        if web_query:

            result = handle_web_request(
                web_query
            )

            print(
                f"Minh Mini > {result}"
            )

            continue

        # --------------------------------
        # AI CHAT
        # --------------------------------

        result = ask_minh(
            message
        )

        print(
            f"Minh Mini > {result}"
        )


if __name__ == "__main__":
    main()
