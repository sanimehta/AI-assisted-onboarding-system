import json
import xml.etree.ElementTree as ET
from pathlib import Path
ALL_DOCS = ['810', '850', '855', '997']
FORMATS = {'xml': 'xml', 'csv': 'csv', 'txt': 'txt'}
TEMPLATE = Path('templates/standard_pattern')
def load_used():
    return json.loads(Path('registry.json').read_text())['used_chains']
def register_chain(chain):
    used = load_used() + [chain]
    Path('registry.json').write_text(json.dumps({'used_chains': used}))
def validate_spec(spec, used_chains):
    errors = []
    chain = spec.get('chain', '')
    if not (chain.isalpha() and chain.isupper() and 3 <= len(chain) <= 5):
        errors.append('chain must be 3 to 5 uppercase letters')
    if chain in used_chains:
        errors.append('chain ' + chain + ' is already in use')
    docs = spec.get('docs', [])
    if not docs:
        errors.append('no documents requested')
    for d in docs:
        if d not in ALL_DOCS:
            errors.append('unsupported doc ' + str(d))
    if spec.get('format') not in FORMATS:
        errors.append('format must be xml, csv, or txt')
    if spec.get('ftp_owner') not in ('customer', 'us'):
        errors.append('ftp_owner must be customer or us')
    name = spec.get('project_name', '')
    if not name or not name.replace('_', '').isalnum():
        errors.append('project_name must be letters, digits, and underscores')
    return errors

def propose_chain(customer_name, used_chains):
    words = customer_name.upper().split()
    letters = [c for c in customer_name.upper() if c.isalpha()]
    initials = ''.join(w[0] for w in words if w[0].isalpha())
    for c in [initials[:5], ''.join(letters[:3]), ''.join(letters[:4]), ''.join(letters[:5])]:
        if 3 <= len(c) <= 5 and c not in used_chains:
            return c
    return None   # a human will have to choose

def check_output(out, spec, written):
    errors = []
    for rel in written:
        text = (out / rel).read_text()
        if '{{' in text or '{{' in rel:
            errors.append('unreplaced placeholder in ' + rel)
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            errors.append('not valid XML: ' + rel)
            continue
        if root.get('chain') != spec['chain']:
            errors.append('chain mismatch in ' + rel)
    expected = {'dataflows/' + d + '_' + spec['chain'] + '.xml' for d in spec['docs']}
    found = {r for r in written if r.startswith('dataflows/')}
    if expected != found:
        errors.append('dataflow files do not match the requested documents')
    return errors

def build_project(spec, used_chains, out_root='projects'):
    errors = validate_spec(spec, used_chains)
    if errors:
        return {'ok': False, 'errors': errors, 'files': []}
    values = {'PROJECT_NAME': spec['project_name'], 'CHAIN': spec['chain'],
              'FTP_OWNER': spec['ftp_owner'], 'FORMAT_EXT': FORMATS[spec['format']]}
    out = Path(out_root) / spec['project_name']
    written = []
    for src in sorted(TEMPLATE.rglob('*')):
        if src.is_dir():
            continue
        rel = src.relative_to(TEMPLATE).as_posix()
        if any(d in rel and d not in spec['docs'] for d in ALL_DOCS):
            continue                      # this document was not requested
        text = src.read_text()
        for k, v in values.items():
            rel = rel.replace('{{' + k + '}}', v)
            text = text.replace('{{' + k + '}}', v)
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text)
        written.append(rel)
    errors = check_output(out, spec, written)
    return {'ok': not errors, 'errors': errors, 'files': written}