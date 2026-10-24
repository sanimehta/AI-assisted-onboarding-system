import sys
from pathlib import Path
from onboard.extract import extract_request
from onboard.generate import build_project, propose_chain, load_used, register_chain

req, retries = extract_request(Path(sys.argv[1]).read_text())
if req is None:
    sys.exit('Could not read the request.')
print(req.model_dump_json(indent=2))
for q in req.questions:
    print('Open question:', q)

fmt = req.format if req.format in ('xml', 'csv', 'txt') else input('Format (xml/csv/txt)? ').strip()
owner = req.ftp_owner if req.ftp_owner in ('customer', 'us') else input('Who hosts the FTP (customer/us)? ').strip()
if input('Is this request correct? (y/n) ').strip().lower() != 'y':
    sys.exit('Stopped. Nothing was built.')

used = load_used()
chain = propose_chain(req.customer_name, used) or input('Choose a chain (3 to 5 letters): ').strip().upper()
name = '_'.join(''.join(c if c.isalnum() else ' ' for c in req.customer_name).split())
spec = {'project_name': name, 'chain': chain, 'docs': sorted(req.docs),
        'format': fmt, 'ftp_owner': owner}
result = build_project(spec, used)
print(result)
if result['ok']:
    register_chain(chain)
    print('Built projects/' + name + ' with chain ' + chain)