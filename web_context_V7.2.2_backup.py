# ============================================================
# MINH MINI V6.2
# WEB CONTEXT
# Lưu và truy xuất các nguồn web gần nhất
# ============================================================

from pathlib import Path
import json
import re


BASE_DIR = Path.home() / "MINH_MINI"
CONTEXT_FILE = BASE_DIR / "memory" / "web_context.json"

MAX_SOURCES = 10


def _ensure_file():
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CONTEXT_FILE.exists():
        CONTEXT_FILE.write_text(
            json.dumps(
                {
                    "query": "",
                    "sources": []
                },
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )


def save_web_results(query, sources):
    """
    Lưu kết quả tìm kiếm web mới nhất.

    sources có thể là:
    [
        {
            "title": "...",
            "url": "..."
        }
    ]

    hoặc danh sách dictionary có thêm field khác.
    """

    _ensure_file()

    clean_sources = []

    for item in sources or []:
        if not isinstance(item, dict):
            continue

        title = str(
            item.get("title")
            or item.get("name")
            or ""
        ).strip()

        url = str(
            item.get("url")
            or item.get("link")
            or ""
        ).strip()

        if not title and not url:
            continue

        clean_sources.append(
            {
                "title": title,
                "url": url
            }
        )

        if len(clean_sources) >= MAX_SOURCES:
            break

    data = {
        "query": str(query or "").strip(),
        "sources": clean_sources
    }

    CONTEXT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return data


def load_web_results():
    _ensure_file()

    try:
        data = json.loads(
            CONTEXT_FILE.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(data, dict):
            return {
                "query": "",
                "sources": []
            }

        return data

    except Exception:
        return {
            "query": "",
            "sources": []
        }


def get_source(number):
    """
    Lấy nguồn theo số.
    Ví dụ:
        get_source(1)
        get_source(2)
    """

    data = load_web_results()
    sources = data.get("sources", [])

    try:
        number = int(number)
    except (TypeError, ValueError):
        return None

    if number < 1 or number > len(sources):
        return None

    return sources[number - 1]


def get_last_source():
    data = load_web_results()
    sources = data.get("sources", [])

    if not sources:
        return None

    return sources[-1]


def get_query():
    data = load_web_results()
    return data.get("query", "")


def format_source(number):
    source = get_source(number)

    if not source:
        data = load_web_results()
        count = len(data.get("sources", []))

        if count == 0:
            return "Hiện chưa có nguồn web nào được lưu."

        return (
            f"Hiện chỉ có {count} nguồn. "
            f"Lam hãy chọn từ nguồn 1 đến nguồn {count}."
        )

    title = source.get("title", "").strip()
    url = source.get("url", "").strip()

    if title and url:
        return (
            f"Nguồn {number}: {title}\n"
            f"Link: {url}"
        )

    if title:
        return f"Nguồn {number}: {title}"

    if url:
        return f"Nguồn {number}: {url}"

    return f"Nguồn {number} không có thông tin chi tiết."


def parse_source_command(message):
    """
    Nhận diện:
        nguồn 1
        nguon 1
        nguồn số 1
        mở nguồn 1
        mở nguon 1
    """

    if not message:
        return None

    text = message.lower().strip()

    patterns = [
        r"^(?:mở\s+)?nguồn\s+số\s+(\d+)$",
        r"^(?:mở\s+)?nguồn\s+(\d+)$",
        r"^(?:mở\s+)?nguon\s+so\s+(\d+)$",
        r"^(?:mở\s+)?nguon\s+(\d+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text)

        if match:
            return int(match.group(1))

    return None


def clear_context():
    save_web_results("", [])