import chat


print("=" * 80)
print("MINH MINI — SYSTEM PROMPT CHECK")
print("=" * 80)

prompt = chat.build_system_prompt()

print()
print("SYSTEM PROMPT:")
print("-" * 80)
print(prompt)
print("-" * 80)

print()
print("LANGUAGE CHECK:")

lower = prompt.lower()

checks = {
    "Vietnamese": [
        "tiếng việt",
        "tiếng Việt",
        "vietnamese",
    ],
    "English": [
        "english",
        "tiếng anh",
    ],
}

for name, words in checks.items():
    found = [
        word
        for word in words
        if word.lower() in lower
    ]

    print(
        f"{name}:",
        found if found else "không thấy",
    )

print()
print("=" * 80)
print("DONE")
print("=" * 80)