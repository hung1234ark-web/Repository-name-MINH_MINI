import os
import gemini_bridge

print("GEMINI_API_KEY:", "PRESENT" if os.environ.get("GEMINI_API_KEY") else "MISSING")
print("HEALTH:", gemini_bridge.health_check())
