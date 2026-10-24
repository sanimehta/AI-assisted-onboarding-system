from dotenv import load_dotenv
load_dotenv('onboarding_agent/.env')
import asyncio, json, sys, time
from google.genai import types
from google.adk.runners import InMemoryRunner
from data.emails import EMAILS
from onboarding_agent.agent import root_agent

TEST = EMAILS[12:] if 'new' in sys.argv else EMAILS
FIELDS = ['customer_name', 'docs', 'format', 'ftp_owner']
DELAY = 5       # seconds between emails (free-tier rate limits)
TIMEOUT = 240   # seconds before one email is counted as failed

def norm(s):
    return ''.join(c for c in (s or '').lower() if c.isalnum())

def clean(v):
    if v is None:
        return None
    v = str(v).strip().lower()
    return None if v in ('null', 'none', 'unknown', '') else v

def parse(text):
    try:
        d = json.loads(text[text.find('{'): text.rfind('}') + 1])
    except Exception:
        return {}
    return {'customer_name': str(d.get('customer_name') or ''),
            'docs': [str(x).strip() for x in (d.get('docs') or [])],
            'format': clean(d.get('format')),
            'ftp_owner': clean(d.get('ftp_owner'))}

def score(pred, gold):
    return {'customer_name': norm(pred.get('customer_name')) == norm(gold['customer_name']),
            'docs': sorted(pred.get('docs') or []) == sorted(gold['docs']),
            'format': pred.get('format') == gold['format'],
            'ftp_owner': pred.get('ftp_owner') == gold['ftp_owner']}

async def run_one(runner, text):
    session = await runner.session_service.create_session(app_name=runner.app_name, user_id='eval')
    msg = types.Content(role='user', parts=[types.Part(text=text)])
    final, model_calls, tool_calls = '', 0, 0
    async for event in runner.run_async(user_id='eval', session_id=session.id, new_message=msg):
        if event.content and event.content.role == 'model':
            model_calls += 1
        tool_calls += len(event.get_function_calls())
        if event.is_final_response() and event.content and event.content.parts:
            final = ''.join(p.text or '' for p in event.content.parts)
    return final, model_calls, tool_calls

async def main():
    runner = InMemoryRunner(agent=root_agent, app_name='eval')
    hits = {f: 0 for f in FIELDS}
    exact = models = tools = 0
    t0 = time.perf_counter()
    for e in TEST:
        try:
            final, mc, tc = await asyncio.wait_for(run_one(runner, e['text']), TIMEOUT)
            pred = parse(final)
        except Exception as ex:
            print('  error', e['id'], str(ex)[:120])
            pred, mc, tc = {}, 0, 0
        ok = score(pred, e['gold'])
        for f in FIELDS:
            hits[f] += ok[f]
        exact += all(ok.values())
        models += mc
        tools += tc
        if not all(ok.values()):
            print('  miss agent', e['id'], [f for f in FIELDS if not ok[f]])
        await asyncio.sleep(DELAY)
    n = len(TEST)
    secs = time.perf_counter() - t0 - DELAY * n
    print('agent', 'exact=%d/%d' % (exact, n), {f: '%d/%d' % (hits[f], n) for f in FIELDS},
          'model_calls/email=%.1f' % (models / n), 'tool_calls/email=%.1f' % (tools / n),
          'secs/email=%.1f' % (secs / n))
    try:
        await runner.close()
    except Exception:
        pass

asyncio.run(main())