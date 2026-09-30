from pathlib import Path
import shutil
import re

path = Path("development_support.py")
backup = Path("development_support.py.before_context_filter_fix")

if not path.exists():
    raise FileNotFoundError(f"Khong tim thay: {path}")

if not backup.exists():
    shutil.copy2(path, backup)
    print(f"BACKUP CREATED: {backup}")
else:
    print(f"BACKUP EXISTS : {backup}")

text = path.read_text(encoding="utf-8")

old = '''    SENSITIVE_NAMES = (
        ".env", ".env.local", ".env.production",
        "credentials", "credential", "secret", "secrets",
        "password", "passwd", "token", "private_key",
        "private-key", "id_rsa",
    )'''

new = '''    SENSITIVE_NAMES = (
        ".env", ".env.local", ".env.production",
        "credentials", "credential", "secret", "secrets",
        "password", "passwd", "token",
        "api_key", "api-key",
        "access_token", "access-token",
        "refresh_token", "refresh-token",
        "authorization",
        "private_key", "private-key", "id_rsa",
    )'''

if old not in text:
    raise RuntimeError(
        "Khong tim thay khoi SENSITIVE_NAMES dung mau mong doi. "
        "Khong sua file de tranh sua nham."
    )

if new in text:
    print("PATCH: ALREADY APPLIED")
else:
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("PATCH: APPLIED")

print("CHECK: development_support.py exists =", path.exists())
