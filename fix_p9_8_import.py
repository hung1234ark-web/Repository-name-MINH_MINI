from pathlib import Path

p = Path("apply_p9_8.py")
s = p.read_text(encoding="utf-8-sig")

old = 'subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)'

new = '''subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""),
        },
    )'''

if old not in s:
    raise RuntimeError("ANCHOR NOT FOUND: subprocess.run")

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8-sig")

print("PATCH REGRESSION IMPORT: PASS")
