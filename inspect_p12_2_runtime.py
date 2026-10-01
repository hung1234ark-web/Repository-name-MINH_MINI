import importlib
import main
import tool_selector

print("=" * 90)
print("P12-2 TOOL SELECTOR RUNTIME DEEP INSPECTION")
print("READ ONLY — NO FILE MODIFICATION")
print("=" * 90)

importlib.invalidate_caches()

runtime = getattr(main, "MINH", None)

print("\n=== MAIN RUNTIME ===")
print("MINH:", type(runtime).__name__)

selector = getattr(runtime, "tool_selector", None)

print("SELECTOR:", type(selector).__name__ if selector is not None else None)
print("SELECTOR MODULE:", type(selector).__module__ if selector is not None else None)

print("\n=== SELECTOR CLASS ===")
print("ToolSelector class:", tool_selector.ToolSelector)
print("ToolSelector module:", tool_selector.ToolSelector.__module__)

print("\n=== DIRECT SELECTOR TEST ===")

message = "tìm thông tin trên web"
decision = {
    "intent": "web",
    "tool": "web",
}
result = {
    "judge": {
        "decision": "proceed",
    }
}

print("MESSAGE:", repr(message))
print("DECISION:", repr(decision))
print("RESULT:", repr(result))

direct = selector.select(
    goal=message,
    plan=None,
    decision=decision,
    result=result,
)

print("\nDIRECT SELECT RESULT:")
print(direct)

print("\n=== _TEXT TEST ===")

text_goal = selector._text(message)
text_decision = selector._text(decision)
text_result = selector._text(result)

print("TEXT GOAL:", repr(text_goal))
print("TEXT DECISION:", repr(text_decision))
print("TEXT RESULT:", repr(text_result))

combined = " ".join(
    part
    for part in (
        text_goal,
        selector._text(None),
        text_decision,
        text_result,
    )
    if part
)

print("\nCOMBINED TEXT:")
print(repr(combined))

print("\n=== WEB TERM TEST ===")

web_terms = (
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

matches = [
    term
    for term in web_terms
    if term in combined
]

print("WEB TERM MATCHES:", matches)
print("WEB MATCH:", bool(matches))

print("\n=== _P11_SELECT_TOOL TEST ===")

p11 = runtime._p11_select_tool(
    goal=message,
    plan=None,
    decision=decision,
    result=result,
)

print("P11 RESULT:")
print(p11)

print("\n=== RUNTIME IDENTITY ===")

print("selector.select:", selector.select)
print("selector.select module:", getattr(selector.select, "__module__", None))
print("selector.select qualname:", getattr(selector.select, "__qualname__", None))

print("\n" + "=" * 90)
print("P12-2 DEEP INSPECTION COMPLETE")
print("NO FILES MODIFIED")
print("=" * 90)
