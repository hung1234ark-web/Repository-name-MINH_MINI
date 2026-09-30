import main

print("=" * 70)
print("MINH MINI - MINH GLOBAL INSPECTION")
print("=" * 70)

print()
print("MINH exists:", hasattr(main, "MINH"))

if hasattr(main, "MINH"):
    print("MINH type:", type(main.MINH))
    print("MINH object:", main.MINH)
else:
    print(">>> [FAIL] main.MINH KHÔNG TỒN TẠI")

print()
print("create_brain exists:", hasattr(main, "create_brain"))
print("MinhMiniCore exists:", hasattr(main, "MinhMiniCore"))

print()
print("=== GLOBAL NAMES RELATED TO MINH ===")

for name in dir(main):
    if "MINH" in name.upper() or "BRAIN" in name.upper():
        print(name)

print()
print("=" * 70)
print(">>> INSPECTION COMPLETE")
print("=" * 70)