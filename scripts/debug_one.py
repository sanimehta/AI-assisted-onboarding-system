import ollama
from data.emails import EMAILS
from onboard.extract import SYSTEM, parse

e = EMAILS[0]
msgs = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': e['text']}]
text = ollama.chat(model='qwen2.5:7b', messages=msgs, options={'temperature': 0}).message.content
print(text)
print(parse(text))