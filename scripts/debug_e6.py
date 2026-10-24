from data.emails import EMAILS
from onboard.library import retrieve

e = next(x for x in EMAILS if x['id'] == 'e6')
for chunk in retrieve(e['text'], exclude_id='e6'):
    print('-', chunk[:120])