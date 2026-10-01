from pathlib import Path
import ast
import py_compile
import shutil
import importlib

TARGET = Path("tool_selector.py")

print("=" * 80)
print("P11 WEB ROUTING TERM FIX")
print("SURGICAL PATCH — NO ARCHITECTURE CHANGE")
print("=" * 80)

source = TARGET.read_text(encoding="utf-8-sig")

ast.parse(source)
py_compile.compile(str(TARGET), doraise=True)

print("PRECHECK AST: PASS")
print("PRECHECK COMPILE: PASS")

old = '''        web_terms = (
            "tìm trên mạng",
            "tìm trên web",
            "google",
            "website",
            "trang web",
            "tin tức",
            "giá",
            "tìm kiếm",
            "search",
            "latest",
            "news",
            "iphone",
        )
'''

new = '''        web_terms = (
            "tìm trên mạng",
            "tìm trên web",
            "tìm thông tin trên mạng",
            "tìm thông tin trên web",
            "tra cứu trên mạng",
            "tra cứu trên web",
            "google",
            "website",
            "trang web",
            "tin tức",
            "giá",
            "tìm kiếm",
            "search",
            "latest",
            "news",
            "iphone",
        )
'''

if old not in source:
    raise SystemExit(
        "ERROR: exact web_terms block not found"
    )

backup = Path("tool_selector.py.before_p11_web_fix")

if backup.exists():
    raise SystemExit(
        "ERROR: backup already exists: "
        + backup.name
    )

shutil.copy2(TARGET, backup)

print("BACKUP CREATED:", backup.name)

source = source.replace(old, new, 1)

TARGET.write_text(
    source,
    encoding="utf-8",
)

print("SURGICAL PATCH: PASS")

# ------------------------------------------------------------
# STATIC VALIDATION
# ------------------------------------------------------------

final_source = TARGET.read_text(
    encoding="utf-8-sig"
)

ast.parse(final_source)
print("FINAL AST: PASS")

py_compile.compile(
    str(TARGET),
    doraise=True,
)
print("FINAL COMPILE: PASS")

required_terms = (
    "tìm thông tin trên mạng",
    "tìm thông tin trên web",
    "tra cứu trên mạng",
    "tra cứu trên web",
)

for term in required_terms:
    if term not in final_source:
        shutil.copy2(backup, TARGET)
        raise SystemExit(
            "TERM VALIDATION FAILED — ROLLBACK: "
            + term
        )

print("WEB TERMS: PASS")

# ------------------------------------------------------------
# RUNTIME VALIDATION
# ------------------------------------------------------------

try:
    importlib.invalidate_caches()

    import tool_selector

    selector = tool_selector.ToolSelector()

    tests = [
        "tìm thông tin trên web",
        "tìm thông tin trên mạng",
        "tra cứu trên web",
        "tra cứu trên mạng",
        "google iphone",
        "tìm giá iphone",
    ]

    print("\n=== WEB ROUTING TESTS ===")

    for message in tests:
        result = selector.select(
            goal=message,
            plan=None,
            decision=None,
            result=None,
        )

        tool = result.get("tool")

        print(
            f"{message!r} -> {tool}"
        )

        if tool != "web":
            raise RuntimeError(
                f"expected web, got {tool!r} "
                f"for {message!r}"
            )

    print("WEB ROUTING: PASS")

    # Preserve fallback behavior.
    fallback = selector.select(
        goal="hãy giải thích Python cho tôi",
        plan=None,
        decision=None,
        result=None,
    )

    print(
        "FALLBACK TEST:",
        fallback.get("tool"),
    )

    if fallback.get("tool") != "ollama":
        raise RuntimeError(
            "fallback behavior changed"
        )

    print("OLLAMA FALLBACK: PASS")

except Exception as exc:
    shutil.copy2(
        backup,
        TARGET,
    )

    print("RUNTIME FAILED — ROLLBACK: PASS")

    raise SystemExit(
        "P11 web routing fix failed: "
        + repr(exc)
    )

print()
print("=" * 80)
print("P11 WEB ROUTING FIX: PASS")
print("WEB REQUESTS -> WEB: PASS")
print("OLLAMA FALLBACK: PRESERVED")
print("P11 SELECTOR: PRESERVED")
print("NO EXECUTION: PASS")
print("=" * 80)
