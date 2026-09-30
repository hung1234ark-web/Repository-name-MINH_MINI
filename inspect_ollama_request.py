import inspect
import web_ai


print("=" * 70)
print("MINH MINI - INSPECT OLLAMA REQUEST")
print("=" * 70)

handler = web_ai.call_ollama

source_lines, start_line = inspect.getsourcelines(handler)

print(f"FILE: {inspect.getsourcefile(handler)}")
print(f"START LINE: {start_line}")
print()

for number, line in enumerate(source_lines, start=start_line):
    print(f"{number:04d}: {line.rstrip()}")

print()
print("=" * 70)
print("END INSPECTION")
print("=" * 70)