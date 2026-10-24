from data.emails import EMAILS
from onboard.library import retrieve

e = next(x for x in EMAILS if x['id'] == 'e4')
for chunk in retrieve(e['text'], exclude_id='e4'):
    print('-', chunk[:150])