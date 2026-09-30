# ============================================================
# MINH MINI — FINAL REPAIR 01
# Sửa các lỗi đã được TOTAL TEST xác nhận
# ============================================================

from pathlib import Path
import re

APP_DIR = Path(r"C:\Users\Admin\MINH_MINI\app")


def log(message):
    print(message)


def repair_main_bom():
    path = APP_DIR / "main.py"

    if not path.exists():
        print("[FAIL] Không tìm thấy main.py")
        return False

    try:
        raw = path.read_bytes()

        # UTF-8 BOM dạng bytes
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
            path.write_bytes(raw)
            print("[FIX] main.py: đã xóa UTF-8 BOM")
            return True

        # U+FEFF đã được decode thành Unicode
        text = raw.decode("utf-8")

        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
            path.write_text(text, encoding="utf-8", newline="")
            print("[FIX] main.py: đã xóa U+FEFF")
            return True

        print("[PASS] main.py: không còn BOM đầu file")
        return True

    except Exception as exc:
        print(f"[FAIL] main.py: {exc}")
        return False


def repair_web_context_duplicate_number():
    path = APP_DIR / "web_context.py"

    if not path.exists():
        print("[FAIL] Không tìm thấy web_context.py")
        return False

    try:
        text = path.read_text(encoding="utf-8")

        # Lỗi đã được TOTAL TEST xác nhận:
        #
        # WebSource(
        #     ...
        #     number=number,
        #     ...
        #     number=number,
        # )
        #
        # Chỉ xóa occurrence thứ hai trong cùng một WebSource(...).

        pattern = re.compile(
            r"return\s+WebSource\s*\((.*?)\)",
            re.DOTALL,
        )

        changed = False

        def fix_block(match):
            nonlocal changed

            block = match.group(0)

            occurrences = list(
                re.finditer(
                    r"(?m)^\s*number\s*=\s*number\s*,\s*$",
                    block,
                )
            )

            if len(occurrences) <= 1:
                return block

            # Giữ occurrence đầu tiên.
            first_end = occurrences[0].end()
            prefix = block[:first_end]
            suffix = block[first_end:]

            # Xóa toàn bộ các occurrence tiếp theo.
            suffix = re.sub(
                r"(?m)^\s*number\s*=\s*number\s*,\s*$",
                "",
                suffix,
            )

            changed = True
            return prefix + suffix

        new_text = pattern.sub(fix_block, text)

        if changed:
            path.write_text(new_text, encoding="utf-8", newline="")
            print("[FIX] web_context.py: đã xóa keyword number bị lặp")
        else:
            print("[PASS] web_context.py: không tìm thấy duplicate number")

        return True

    except Exception as exc:
        print(f"[FAIL] web_context.py: {exc}")
        return False


def inspect_response_guard():
    path = APP_DIR / "response_guard.py"

    if not path.exists():
        print("[FAIL] Không tìm thấy response_guard.py")
        return False

    try:
        text = path.read_text(encoding="utf-8")

        print()
        print("----- RESPONSE GUARD SELF-CHECK SOURCE -----")

        lines = text.splitlines()

        for index, line in enumerate(lines, start=1):
            lowered = line.lower()

            if (
                "empty_protection" in lowered
                or "self_check" in lowered
                or "empty" in lowered
            ):
                start = max(1, index - 3)
                end = min(len(lines), index + 8)

                print(f"\n--- dòng {start} → {end} ---")

                for number in range(start, end + 1):
                    print(
                        f"{number:04d}: "
                        f"{lines[number - 1]}"
                    )

        print("--------------------------------------------")
        print()

        return True

    except Exception as exc:
        print(f"[FAIL] Đọc response_guard.py: {exc}")
        return False


def inspect_router_guard():
    path = APP_DIR / "router_guard.py"

    if not path.exists():
        print("[FAIL] Không tìm thấy router_guard.py")
        return False

    try:
        text = path.read_text(encoding="utf-8")

        print()
        print("----- ROUTER GUARD ACTION LOGIC -----")

        lines = text.splitlines()

        for index, line in enumerate(lines, start=1):
            lowered = line.lower()

            if any(
                key in lowered
                for key in (
                    "action",
                    "is_action",
                    "open",
                    "close",
                    "known_intents",
                    "validate_route",
                )
            ):
                start = max(1, index - 2)
                end = min(len(lines), index + 4)

                print(f"\n--- dòng {start} → {end} ---")

                for number in range(start, end + 1):
                    print(
                        f"{number:04d}: "
                        f"{lines[number - 1]}"
                    )

        print("------------------------------------")
        print()

        return True

    except Exception as exc:
        print(f"[FAIL] Đọc router_guard.py: {exc}")
        return False


def syntax_check():
    import ast

    print()
    print("----- SYNTAX CHECK -----")

    ok = True

    for filename in (
        "main.py",
        "web_context.py",
        "response_guard.py",
        "router_guard.py",
    ):
        path = APP_DIR / filename

        try:
            source = path.read_text(encoding="utf-8")

            ast.parse(
                source,
                filename=str(path),
            )

            print(f"[PASS] syntax:{filename}")

        except Exception as exc:
            print(f"[FAIL] syntax:{filename}")
            print(f"       {exc}")
            ok = False

    return ok


def main():
    print("=" * 60)
    print("MINH MINI — FINAL REPAIR 01")
    print("=" * 60)
    print(f"APP : {APP_DIR}")
    print()

    print("=== 01. MAIN BOM ===")
    repair_main_bom()

    print()
    print("=== 02. WEB CONTEXT DUPLICATE ===")
    repair_web_context_duplicate_number()

    print()
    print("=== 03. RESPONSE GUARD DIAGNOSTIC ===")
    inspect_response_guard()

    print()
    print("=== 04. ROUTER GUARD DIAGNOSTIC ===")
    inspect_router_guard()

    print()
    print("=== 05. SYNTAX AFTER REPAIR ===")
    syntax_check()

    print()
    print("=" * 60)
    print("REPAIR 01 HOÀN TẤT")
    print("=" * 60)
    print()
    print("Chưa sửa mù response_guard/router_guard.")
    print("Script chỉ sửa 2 lỗi chắc chắn và in đúng đoạn")
    print("cần sửa tiếp để tránh phá kiến trúc FINAL.")


if __name__ == "__main__":
    main()