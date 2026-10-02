import os
from gemini_bridge import ask
key = os.getenv('GEMINI_API_KEY')
print('KEY_PRESENT:', bool(key))
r = ask('Reply with exactly: MINH_GEMINI_OK')
print('OK:', r.get('ok'))
print('TEXT:', r.get('text'))
print('ERROR:', r.get('error'))
