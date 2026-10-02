import os, httpx
key=os.getenv('GEMINI_API_KEY')
base='https://generativelanguage.googleapis.com/v1beta'
models=['gemini-3.8-flash-lite','gemini-3.7-flash','gemini-3.6-flash','gemini-3.5-flash','gemini-3.1-flash-lite']
for model in models:
    try:
        r=httpx.post(f'{base}/models/{model}:generateContent',params={'key':key},json={'contents':[{'parts':[{'text':'Reply with exactly: MINH_GEMINI_OK'}]}]},timeout=20)
        print(model, r.status_code, end=' ')
        if r.status_code==200:
            data=r.json(); print(data.get('candidates',[{}])[0].get('content',{}).get('parts',[{}])[0].get('text','')); break
        else: print(r.text[:180])
    except Exception as e: print(type(e).__name__, str(e)[:120])
