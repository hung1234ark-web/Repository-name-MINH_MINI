from pathlib import Path

path = Path("test_development_support_e2e.py")
text = path.read_text(encoding="utf-8")

old = '''        change_request = support.create_change_request(
            task_id=task_id,
            title="E2E Change Request",
            reason=(
                "Test whether contract changes require "
                "explicit resolution."
            ),
            requested_changes=[
                "Allow an additional development file."
            ],
        )'''

new = '''        change_request = support.create_change_request(
            task_id=task_id,
            reason=(
                "Test whether contract changes require "
                "explicit resolution."
            ),
            requested_changes=[
                "Allow an additional development file."
            ],
        )'''

if old not in text:
    raise RuntimeError(
        "Khong tim thay dung doan create_change_request trong E2E. "
        "Khong sua file."
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("PATCH: PASS")
print("REMOVED: unsupported title= argument")
