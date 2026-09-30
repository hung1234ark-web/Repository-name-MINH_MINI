from pathlib import Path
import shutil
import re


APP_DIR = Path(r"C:\Users\Admin\MINH_MINI\app")
MAIN_FILE = APP_DIR / "main.py"
BACKUP_FILE = APP_DIR / "main_before_chat_integration.py"


CHAT_IMPORT = 'chat_module = safe_import("chat")'


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def find_build_handlers(source: str) -> tuple[int, int]:
    """
    Tìm chính xác function build_handlers() bằng cấu trúc def
    và indentation, không phụ thuộc nội dung bên trong.
    """

    match = re.search(
        r"(?m)^def\s+build_handlers\s*\([^)]*\)\s*->\s*dict\[str,\s*Any\]\s*:",
        source,
    )

    if not match:
        fail("Không tìm thấy hàm build_handlers().")

    start = match.start()

    # Tìm function kế tiếp ở cấp 0.
    next_function = re.search(
        r"(?m)^def\s+\w+\s*\(",
        source[match.end():],
    )

    if next_function:
        end = match.end() + next_function.start()
    else:
        end = len(source)

    return start, end


def add_chat_import(source: str) -> str:

    if CHAT_IMPORT in source:
        print("[PASS] chat_module đã tồn tại")
        return source

    # Ưu tiên chèn ngay sau web_context.
    pattern = re.compile(
        r'(?m)^(?P<indent>\s*)web_context\s*=\s*safe_import\(\s*["\']web_context["\']\s*\)\s*$'
    )

    match = pattern.search(source)

    if match:
        indent = match.group("indent")

        replacement = (
            match.group(0)
            + "\n"
            + indent
            + CHAT_IMPORT
        )

        source = (
            source[:match.start()]
            + replacement
            + source[match.end():]
        )

        print("[PASS] Đã thêm chat_module")
        return source

    # Nếu không có web_context thì chèn trước class MinhMiniCore.
    class_match = re.search(
        r"(?m)^class\s+MinhMiniCore\b",
        source,
    )

    if class_match:
        source = (
            source[:class_match.start()]
            + CHAT_IMPORT
            + "\n\n\n"
            + source[class_match.start():]
        )

        print("[PASS] Đã thêm chat_module")
        return source

    fail(
        "Không tìm được vị trí an toàn để thêm chat_module."
    )


def replace_build_handlers(source: str) -> str:

    start, end = find_build_handlers(source)

    old_block = source[start:end]

    # Kiểm tra source thực tế trước khi thay.
    required_keys = [
        '"chat"',
        '"ollama"',
    ]

    for key in required_keys:
        if key not in old_block:
            fail(
                f"build_handlers() không chứa key {key}."
            )

    new_block = '''def build_handlers() -> dict[str, Any]:

    return {
        "action": handle_action,
        "web": handle_web,
        "web_ai": handle_web,
        "web_context": handle_web_context,
        "memory": handle_memory,
        "time": lambda **kwargs: current_time(),
        "date": lambda **kwargs: current_date(),
        "chat": chat_module.handle_chat,
        "ollama": chat_module.handle_chat,
    }

'''

    source = (
        source[:start]
        + new_block
        + source[end:]
    )

    print(
        "[PASS] build_handlers() đã chuyển chat/ollama sang chat.py"
    )

    return source


def main() -> None:

    print("=" * 70)
    print("MINH MINI - CHAT INTEGRATION FINAL V2")
    print("=" * 70)

    if not MAIN_FILE.exists():
        fail(
            f"Không tìm thấy: {MAIN_FILE}"
        )

    source = MAIN_FILE.read_text(
        encoding="utf-8",
        errors="replace",
    )

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    shutil.copy2(
        MAIN_FILE,
        BACKUP_FILE,
    )

    print(
        f"[PASS] Backup: {BACKUP_FILE.name}"
    )

    # --------------------------------------------------------
    # ADD CHAT MODULE
    # --------------------------------------------------------

    source = add_chat_import(source)

    # --------------------------------------------------------
    # REPLACE BUILD HANDLERS
    # --------------------------------------------------------

    source = replace_build_handlers(source)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    MAIN_FILE.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    print("[PASS] Đã ghi main.py")

    print("=" * 70)
    print(">>> CHAT INTEGRATION FINAL V2: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()