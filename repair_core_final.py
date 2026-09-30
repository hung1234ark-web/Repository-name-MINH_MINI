from pathlib import Path
import re
import shutil
import importlib.util


BASE_DIR = Path(__file__).resolve().parent
MAIN_FILE = BASE_DIR / "main.py"


def read_text(path):
    return path.read_text(encoding="utf-8")


def write_text(path, text):
    path.write_text(text, encoding="utf-8")


def backup_main():
    backup = BASE_DIR / "main_before_core_restore.py"
    shutil.copy2(MAIN_FILE, backup)
    print(f"[PASS] Backup: {backup.name}")


def find_function_block(source, name):
    pattern = re.compile(
        rf"(?m)^def {re.escape(name)}\(.*?(?=^def |\Z)",
        re.DOTALL,
    )

    match = pattern.search(source)

    if not match:
        return None

    return match.group(0).rstrip() + "\n"


def find_class_block(source, name):
    pattern = re.compile(
        rf"(?m)^class {re.escape(name)}(?:\([^)]*\))?:.*?(?=^class |^def |\Z)",
        re.DOTALL,
    )

    match = pattern.search(source)

    if not match:
        return None

    return match.group(0).rstrip() + "\n"


def load_backup_candidates():
    candidates = []

    for path in sorted(
        BASE_DIR.glob("main*.py"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        if path.name == "main.py":
            continue

        if "backup" in path.name.lower():
            candidates.append(path)

        if "before" in path.name.lower():
            candidates.append(path)

    unique = []

    for path in candidates:
        if path not in unique:
            unique.append(path)

    return unique


def inspect_candidates():
    print()
    print("=" * 70)
    print("=== CORE BACKUP SEARCH ===")
    print("=" * 70)

    candidates = load_backup_candidates()

    if not candidates:
        print("[FAIL] Không tìm thấy main backup.")
        return []

    for path in candidates:
        try:
            source = read_text(path)

            has_class = bool(
                re.search(
                    r"(?m)^class MinhMiniCore\b",
                    source,
                )
            )

            has_minh = bool(
                re.search(
                    r"(?m)^MINH\s*=",
                    source,
                )
            )

            print(
                f"[{'FOUND' if has_class else 'MISS'}] "
                f"{path.name} | "
                f"MinhMiniCore={has_class} | "
                f"MINH={has_minh}"
            )

        except Exception as exc:
            print(
                f"[WARN] {path.name}: {exc}"
            )

    return candidates


def extract_best_core(candidates):
    best = None
    best_score = -1

    for path in candidates:
        try:
            source = read_text(path)

            class_block = find_class_block(
                source,
                "MinhMiniCore",
            )

            if not class_block:
                continue

            score = 0

            for name in (
                "process",
                "complete_input",
                "execute_decision",
                "make_clarification",
                "status",
            ):
                if re.search(
                    rf"(?m)^\s+def {re.escape(name)}\(",
                    class_block,
                ):
                    score += 1

            if "MINH" in source:
                score += 2

            if score > best_score:
                best_score = score
                best = (
                    path,
                    source,
                    class_block,
                )

        except Exception:
            continue

    return best


def ensure_minh_object(source):
    if re.search(
        r"(?m)^MINH\s*=",
        source,
    ):
        return source, False

    candidates = [
        "\nMINH = MinhMiniCore()\n",
        "\nMINH = MinhMiniCore\n",
    ]

    for candidate in candidates:
        if "MinhMiniCore" in source:
            return (
                source.rstrip()
                + candidate,
                True,
            )

    return source, False


def restore_core():
    current = read_text(MAIN_FILE)

    candidates = inspect_candidates()

    result = extract_best_core(candidates)

    if result is None:
        print()
        print(
            "[FAIL] Không tìm thấy backup chứa "
            "MinhMiniCore."
        )
        print(
            "Không tự dựng Core mới để tránh làm hỏng kiến trúc."
        )
        return False

    backup_path, backup_source, class_block = result

    print()
    print(
        f"[PASS] Chọn backup Core: "
        f"{backup_path.name}"
    )

    if re.search(
        r"(?m)^class MinhMiniCore\b",
        current,
    ):
        print(
            "[PASS] MinhMiniCore hiện đã tồn tại."
        )
    else:
        insert_position = None

        markers = [
            "def main(",
            "def self_check(",
            "def status(",
        ]

        for marker in markers:
            match = re.search(
                rf"(?m)^{re.escape(marker)}",
                current,
            )

            if match:
                insert_position = match.start()
                break

        if insert_position is None:
            print(
                "[FAIL] Không tìm thấy vị trí an toàn "
                "để chèn MinhMiniCore."
            )
            return False

        current = (
            current[:insert_position]
            + class_block
            + "\n\n"
            + current[insert_position:]
        )

        print(
            "[PASS] Đã phục hồi class MinhMiniCore."
        )

    current, added_minh = ensure_minh_object(
        current
    )

    if added_minh:
        print(
            "[PASS] Đã phục hồi object MINH."
        )
    else:
        print(
            "[PASS] Object MINH đã tồn tại."
        )

    write_text(
        MAIN_FILE,
        current,
    )

    return True


def verify():
    print()
    print("=" * 70)
    print("=== CORE FINAL VERIFICATION ===")
    print("=" * 70)

    source = read_text(MAIN_FILE)

    checks = {
        "MinhMiniCore": bool(
            re.search(
                r"(?m)^class MinhMiniCore\b",
                source,
            )
        ),
        "MINH": bool(
            re.search(
                r"(?m)^MINH\s*=",
                source,
            )
        ),
        "process": "def process(" in source,
        "status": "def status(" in source,
        "chat_module": "chat_module" in source,
    }

    all_pass = True

    for name, ok in checks.items():
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}"
        )

        if not ok:
            all_pass = False

    return all_pass


def main():
    print()
    print("=" * 70)
    print("MINH MINI — CORE FINAL RESTORE")
    print("=" * 70)

    if not MAIN_FILE.exists():
        print(
            "[FAIL] Không tìm thấy main.py."
        )
        return

    backup_main()

    if not restore_core():
        print()
        print(
            ">>> CORE RESTORE: STOP"
        )
        return

    if verify():
        print()
        print(
            ">>> CORE RESTORE: PASS"
        )
    else:
        print()
        print(
            ">>> CORE RESTORE: FAIL"
        )


if __name__ == "__main__":
    main()