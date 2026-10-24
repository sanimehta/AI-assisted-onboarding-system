import time
from dotenv import load_dotenv
import os
load_dotenv("onboarding_agent/.env")
from google import genai
from google.genai import types

client = genai.Client(
    api_key=os.environ["GOOGLE_API_KEY"],
    http_options=types.HttpOptions(timeout=15000),
)

names = [
    m.name.replace("models/", "")
    for m in client.models.list()
    if "generateContent" in (m.supported_actions or [])
    and "flash" in m.name
]
print("Flash models on your key:", names)

for name in names:
    t = time.time()
    try:
        r = client.models.generate_content(model=name, contents="Say hi")
        print(f"OK   {name}: {round(time.time() - t, 1)}s")
    except Exception as e:
        print(f"FAIL {name}: {str(e)[:100]}")