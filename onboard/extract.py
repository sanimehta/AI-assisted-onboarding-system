import json
import ollama
from pydantic import BaseModel
from .generate import ALL_DOCS

MODEL = 'qwen2.5:7b'

SYSTEM = '''You read customer emails that request electronic document onboarding and extract the request.
Document codes: 810 = invoice, 850 = purchase order, 855 = purchase order acknowledgement (also called order confirmation), 997 = functional acknowledgement.
Return ONLY a JSON object with these keys:
customer_name (string), docs (list of codes as strings), format (xml, csv, or txt; null if not stated), ftp_owner (customer if the customer hosts the server or will provide the login details; us if the customer wants us to host it or will pull files from us; null if not stated), questions (list of things you could not determine).
Never guess. Use null and add a question when something is not stated.'''

class Request(BaseModel):
    customer_name: str = ''
    docs: list[str] = []
    format: str | None = None
    ftp_owner: str | None = None
    questions: list[str] = []

def clean(value):
    if value is None:
        return None
    v = str(value).strip().lower()
    return None if v in ('null', 'none', 'unknown', '') else v

def parse(text):
    data = json.loads(text[text.find('{'): text.rfind('}') + 1])
    return Request(
        customer_name=str(data.get('customer_name') or ''),
        docs=[str(d).strip() for d in (data.get('docs') or [])],
        format=clean(data.get('format')),
        ftp_owner=clean(data.get('ftp_owner')),
        questions=[str(q) for q in (data.get('questions') or [])],
    )

def problems(req):
    out = []
    for d in req.docs:
        if d not in ALL_DOCS:
            out.append('unknown document code ' + d)
    if req.format not in (None, 'xml', 'csv', 'txt'):
        out.append('format must be xml, csv, txt, or null')
    if req.ftp_owner not in (None, 'customer', 'us'):
        out.append('ftp_owner must be customer, us, or null')
    return out

def extract_request(email, examples=''):
    '''Return (request or None, number of retries used).'''
    messages = [{'role': 'system', 'content': SYSTEM + examples},
                {'role': 'user', 'content': email}]
    req = None
    for attempt in range(2):
        text = ollama.chat(model=MODEL, messages=messages, options={'temperature': 0}).message.content or ''
        try:
            req = parse(text)
            issues = problems(req)
        except Exception:
            req, issues = None, ['the answer was not valid JSON']
        if not issues:
            return req, attempt
        messages.append({'role': 'assistant', 'content': text})
        messages.append({'role': 'user', 'content': 'Fix these problems and answer again: ' + '; '.join(issues)})
    return req, 1