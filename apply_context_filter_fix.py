from pathlib import Path

path = Path("development_support.py")
text = path.read_text(encoding="utf-8")

old = '''        "password",
        "passwd",
        "token",
        "private_key",'''

new = '''        "password",
        "passwd",
        "token",
        "api_key",
        "api-key",
        "access_token",
        "access-token",
        "refresh_token",
        "refresh-token",
        "authorization",
        "private_key",'''

if old not in text:
    raise RuntimeError(
        "Khong tim thay vi tri can sua. "
        "Khong thay doi development_support.py."
    )

if '"api_key",' in text:
    print("PATCH: ALREADY APPLIED")
else:
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("PATCH: APPLIED")

print("FILE:", path)
