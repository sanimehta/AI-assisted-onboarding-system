import sys, time
from data.emails import EMAILS
from onboard.extract import extract_request
from onboard.rules_baseline import rules_extract

USE_RAG = 'rag' in sys.argv
FIELDS = ['customer_name', 'docs', 'format', 'ftp_owner']
TEST = EMAILS[12:] if 'new' in sys.argv else EMAILS
def norm(s):
    return ''.join(c for c in (s or '').lower() if c.isalnum())

def score(pred, gold, fields):
    ok = {}
    if 'customer_name' in fields:
        ok['customer_name'] = norm(pred.get('customer_name')) == norm(gold['customer_name'])
    ok['docs'] = sorted(pred.get('docs') or []) == sorted(gold['docs'])
    ok['format'] = pred.get('format') == gold['format']
    ok['ftp_owner'] = pred.get('ftp_owner') == gold['ftp_owner']
    return ok

def llm_pred(e, rag=False):
    examples = ''
    if rag:
        from onboard.library import retrieve
        examples = ' Reference notes and similar past requests: ' + ' --- '.join(retrieve(e['text'], exclude_id=e['id']))
    req, retries = extract_request(e['text'], examples)
    return (req.model_dump() if req else {}), retries

systems = [('rules', lambda e: (rules_extract(e['text']), 0), FIELDS[1:]),
           ('llm', lambda e: llm_pred(e), FIELDS)]
if USE_RAG:
    systems.append(('llm+rag', lambda e: llm_pred(e, True), FIELDS))

for name, fn, fields in systems:
    hits = {f: 0 for f in fields}
    exact = retries_total = 0
    t0 = time.perf_counter()
    for e in TEST:
        pred, retries = fn(e)
        ok = score(pred, e['gold'], fields)
        for f in fields:
            hits[f] += ok[f]
        exact += all(ok.values())
        retries_total += retries
        if not all(ok.values()):
            print('  miss', name, e['id'], [f for f in fields if not ok[f]])
    n = len(TEST)
    secs = time.perf_counter() - t0
    print(name, 'exact=%d/%d' % (exact, n), {f: '%d/%d' % (hits[f], n) for f in fields},
          'retries=%d' % retries_total, 'secs/email=%.1f' % (secs / n))