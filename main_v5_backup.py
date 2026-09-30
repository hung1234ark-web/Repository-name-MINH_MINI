import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime

from action import handle_action_command
from web import safe_search
from web_ai import summarize_results


# ============================================================
# MINH MINI - MAIN V5.0
# ROUTER + MEMORY + TYPO + WEB + OLLAMA
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path.home() / "MINH_MINI"

MEMORY_FILE = (
    BASE_DIR
    / "memory"
    / "memory.json"
)

CONFIG_FILE = (
    BASE_DIR
    / "config"
    / "config.json"
)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def remove_accents(text):
    text = unicodedata.normalize(
        "NFD",
        text
    )

    return "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )


def normalize_spaces(text):
    return " ".join(
        str(text).strip().split()
    )


def normalize_text(text):
    """
    Chuẩn hóa để router hiểu:
    - tiếng Việt có dấu / không dấu
    - khoảng trắng thừa
    - một số typo phổ biến
    """

    text = normalize_spaces(text)

    # Một số lỗi gõ phổ biến
    replacements = {
        "mấy h": "mấy giờ",
        "may h": "may gio",
        "mấy g": "mấy giờ",
        "may g": "may gio",

        "moi nhat": "mới nhất",
        "moi nhấ": "mới nhất",

        "sau rieng": "sầu riêng",
        "saurieng": "sầu riêng",
        "sầu riềng": "sầu riêng",

        "mang cut": "măng cụt",
        "mang cutt": "măng cụt",
        "mangcut": "măng cụt",

        "gía": "giá",
        "gí": "giá",
        "giaa": "giá",

        "iphon": "iphone",
        "ipone": "iphone",
        "iphonee": "iphone",

        "bao nhieu": "bao nhiêu",
        "hien tai": "hiện tại",
        "hom nay": "hôm nay",
        "tim kiem": "tìm kiếm",
        "tra cuu": "tra cứu",
    }

    result = text

    for wrong, correct in replacements.items():
        result = re.sub(
            re.escape(wrong),
            correct,
            result,
            flags=re.IGNORECASE
        )

    return normalize_spaces(result)


def key_text(text):
    """
    Dùng để so sánh câu lệnh.
    Ví dụ:
    'Xem bộ nhớ'
    'xem bo nho'
    ' XEM   BỘ NHỚ '
    đều thành cùng một dạng.
    """

    text = normalize_text(text)

    text = remove_accents(
        text.lower()
    )

    return normalize_spaces(text)


# ============================================================
# MEMORY
# ============================================================

def load_memory():

    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not MEMORY_FILE.exists():

        MEMORY_FILE.write_text(
            "[]",
            encoding="utf-8"
        )

    try:

        data = json.loads(
            MEMORY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


memory = load_memory()


def save_memory():

    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MEMORY_FILE.write_text(
        json.dumps(
            memory,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def remember(text):

    global memory

    text = normalize_spaces(text)

    if not text:
        return False

    new_key = key_text(text)

    for item in memory:

        if key_text(item) == new_key:
            return False

    memory.append(text)

    save_memory()

    return True


def forget_memory(text):

    global memory

    text = normalize_spaces(text)

    if not text:
        return None

    target = key_text(text)

    for item in memory[:]:

        if key_text(item) == target:

            memory.remove(item)

            save_memory()

            return item

    return None


def clear_memory():

    global memory

    memory = []

    save_memory()


# ============================================================
# MEMORY COMMAND ROUTER
# ============================================================

def handle_memory_command(message):

    text = normalize_text(message)

    normalized = key_text(text)

    # --------------------------------------------------------
    # XEM BỘ NHỚ
    # --------------------------------------------------------

    view_commands = {

        "xem bo nho",
        "xem memory",
        "show memory",
        "kiem tra bo nho",
        "kiem tra du lieu",
        "xem du lieu",
        "mo bo nho",
        "mo memory",
        "hien thi bo nho",
        "hien thi memory",
    }

    if normalized in view_commands:

        if not memory:

            return (
                True,
                "Hiện tại Minh chưa nhớ điều gì."
            )

        lines = [
            "Những điều Minh đang nhớ:"
        ]

        for index, item in enumerate(
            memory,
            1
        ):

            lines.append(
                f"{index}. {item}"
            )

        return (
            True,
            "\n".join(lines)
        )

    # --------------------------------------------------------
    # XÓA TOÀN BỘ
    # --------------------------------------------------------

    clear_commands = {

        "xoa tat ca bo nho",
        "xoa het bo nho",
        "xoa bo nho",
        "xoa tat ca du lieu",
        "xoa het du lieu",
        "clear memory",
        "xoa memory",
    }

    if normalized in clear_commands:

        clear_memory()

        return (
            True,
            "Minh đã xóa toàn bộ bộ nhớ."
        )

    # --------------------------------------------------------
    # NHỚ
    # --------------------------------------------------------

    remember_patterns = [
        r"^nhớ\s+(.+)$",
        r"^nho\s+(.+)$",
        r"^lưu\s+(.+)$",
        r"^luu\s+(.+)$",
        r"^ghi nhớ\s+(.+)$",
        r"^ghi nho\s+(.+)$",
    ]

    for pattern in remember_patterns:

        match = re.match(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            content = (
                match.group(1)
                .strip()
            )

            if not content:

                return (
                    True,
                    "Lam muốn Minh nhớ điều gì?"
                )

            if remember(content):

                return (
                    True,
                    f"Minh nhớ rồi nha: {content}"
                )

            return (
                True,
                "Điều này Minh đã nhớ rồi."
            )

    # --------------------------------------------------------
    # QUÊN / XÓA MỘT MỤC
    # --------------------------------------------------------

    forget_patterns = [
        r"^quên rằng\s+(.+)$",
        r"^quen rang\s+(.+)$",
        r"^quên\s+(.+)$",
        r"^quen\s+(.+)$",
        r"^xóa\s+(.+)$",
        r"^xoa\s+(.+)$",
        r"^sóa\s+(.+)$",
        r"^soa\s+(.+)$",
    ]

    for pattern in forget_patterns:

        match = re.match(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            content = (
                match.group(1)
                .strip()
            )

            if not content:

                return (
                    True,
                    "Lam muốn Minh quên điều gì?"
                )

            deleted = forget_memory(
                content
            )

            if deleted is not None:

                return (
                    True,
                    f"Minh đã quên: {deleted}"
                )

            return (
                True,
                "Minh không tìm thấy điều đó trong bộ nhớ."
            )

    return False, None


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

    normalized = key_text(message)

    time_patterns = (
        "may gio roi",
        "bay gio may gio",
        "bay gio la may gio",
        "may gio",
        "gio hien tai",
        "hien tai may gio",
        "xem gio",
    )

    date_patterns = (
        "hom nay ngay bao nhieu",
        "hom nay ngay may",
        "hom nay la ngay may",
        "hom nay thu may",
        "hom nay la thu may",
        "ngay hom nay",
        "xem ngay",
    )

    for pattern in time_patterns:

        if normalized == pattern:
            return (
                True,
                get_current_time()
            )

    for pattern in date_patterns:

        if normalized == pattern:
            return (
                True,
                get_current_date()
            )

    return False, None


# ============================================================
# YOUTUBE SEARCH
# ============================================================

def extract_youtube_search(message):

    text = normalize_text(message)

    patterns = [

        r"(?:mở|mo)\s+(?:ytb|youtube)\s+(?:và\s+)?(?:tìm|tim|tìm kiếm|tim kiem)\s+(.+)",

        r"(?:mở|mo)\s+(?:ytb|youtube)\s+(.+?)\s+(?:trong|trên|tren)\s+youtube",

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

            query = (
                match.group(1)
                .strip()
            )

            if query:
                return query

    return None


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


# ============================================================
# FACEBOOK
# ============================================================

def open_facebook():

    import webbrowser

    webbrowser.open(
        "https://www.facebook.com"
    )

    return "Minh đã mở Facebook."


# ============================================================
# CUSTOM ACTION ROUTER
# ============================================================

def handle_custom_actions(message):

    text = normalize_text(message)

    normalized = key_text(text)

    # --------------------------------------------------------
    # TIME / DATE
    # --------------------------------------------------------

    handled, result = handle_time_date(
        text
    )

    if handled:
        return True, result

    # --------------------------------------------------------
    # YOUTUBE SEARCH
    # --------------------------------------------------------

    youtube_query = extract_youtube_search(
        text
    )

    if youtube_query:

        return (
            True,
            open_youtube_search(
                youtube_query
            )
        )

    # --------------------------------------------------------
    # FACEBOOK
    # --------------------------------------------------------

    facebook_commands = {

        "mo facebook",
        "mo fb",
        "truy cap facebook",
        "truy cap fb",
        "vao facebook",
        "vao fb",
    }

    if normalized in facebook_commands:

        return (
            True,
            open_facebook()
        )

    # --------------------------------------------------------
    # ACTION.PY
    # --------------------------------------------------------

    handled, result = handle_action_command(
        text
    )

    if handled:
        return True, result

    return False, None


# ============================================================
# WEB ROUTER
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

    text = normalize_text(message)

    if not text:
        return None

    handled, _ = handle_time_date(
        text
    )

    if handled:
        return None

    normalized = key_text(text)

    for keyword in WEB_KEYWORDS:

        keyword_key = key_text(
            keyword
        )

        if keyword_key in normalized:
            return text

    return None


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
                "Minh không tìm thấy "
                "kết quả phù hợp."
            )

        answer = summarize_results(
            query,
            results
        )

        if not answer:

            return (
                "Minh tìm thấy kết quả "
                "nhưng chưa tạo được câu trả lời."
            )

        return answer

    except Exception as error:

        return (
            "Minh gặp lỗi khi kiểm tra web: "
            f"{error}"
        )


# ============================================================
# OLLAMA CONFIG
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


# ============================================================
# OLLAMA CHAT
# ============================================================

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

        if not endpoint.endswith(
            "/api/chat"
        ):

            endpoint += "/api/chat"

        memory_context = ""

        if memory:

            memory_context = (
                "\nThông tin Lam đã cho Minh nhớ:\n"
                + "\n".join(
                    f"- {item}"
                    for item in memory[-20:]
                )
            )

        prompt = f"""
Lam đang nói chuyện với Minh Mini.

Quy tắc:
- Gọi người dùng là Lam.
- Minh tự xưng là Minh.
- Không gọi Lam là "bạn".
- Trả lời bằng tiếng Việt tự nhiên.
- Không tự nhận đã thực hiện một hành động
  nếu chương trình chưa thực hiện hành động đó.
- Không bịa thông tin.
- Nếu câu hỏi đơn giản thì trả lời ngắn gọn.
- Nếu Lam đang nói chuyện bình thường thì trò chuyện tự nhiên.
- Không tự biến câu nói bình thường thành lệnh máy tính.

{memory_context}

Tin nhắn hiện tại của Lam:
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

        result = (
            data
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not result:

            return (
                "Minh chưa nhận được câu trả lời "
                "từ bộ não AI."
            )

        return result

    except Exception as error:

        return (
            "Minh chưa thể kết nối bộ não AI "
            f"lúc này. Lỗi: {error}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 55)
    print("              MINH MINI")
    print("                 V5.0")
    print("=" * 55)

    print("Xin chào Lam!")
    print("Minh Mini đã khởi động.")
    print("Gõ 'thoat' để đóng.")
    print()

    while True:

        try:

            message = input(
                "Lam > "
            ).strip()

        except KeyboardInterrupt:

            print()
            print(
                "Minh Mini tạm biệt Lam!"
            )

            break

        except EOFError:

            print()
            print(
                "Minh Mini tạm biệt Lam!"
            )

            break

        # ----------------------------------------------------
        # BỎ QUA INPUT RỖNG
        # ----------------------------------------------------

        if not message:
            continue

        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if key_text(message) in (
            "thoat",
            "exit",
            "quit",
        ):

            print(
                "Minh Mini tạm biệt Lam!"
            )

            break

        # ----------------------------------------------------
        # NORMALIZE
        # ----------------------------------------------------

        message = normalize_text(
            message
        )

        # ----------------------------------------------------
        # 1. MEMORY
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 2. CUSTOM ACTIONS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 3. WEB
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 4. AI CHAT
        # ----------------------------------------------------

        result = ask_minh(
            message
        )

        print(
            f"Minh Mini > {result}"
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()