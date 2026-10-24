import tempfile
from onboard.generate import build_project, load_used

base = {'project_name': 'NewCo_Foods', 'chain': 'NCF', 'docs': ['810', '855'],
        'format': 'xml', 'ftp_owner': 'customer'}
CASES = [
    ('good: two docs', dict(base), True),
    ('good: all docs as csv', dict(base, chain='NCFD', docs=['810', '850', '855', '997'], format='csv'), True),
    ('good: we host the ftp', dict(base, chain='NCFE', ftp_owner='us'), True),
    ('good: one doc', dict(base, chain='NCFF', docs=['997']), True),
    ('bad: chain too long', dict(base, chain='NEWCOF'), False),
    ('bad: lowercase chain', dict(base, chain='ncf'), False),
    ('bad: chain already used', dict(base, chain='ACM'), False),
    ('bad: unsupported doc', dict(base, docs=['810', '999']), False),
    ('bad: no docs', dict(base, docs=[]), False),
    ('bad: unknown format', dict(base, format='json'), False),
]

used = load_used()
passed = 0
for name, spec, expect_ok in CASES:
    with tempfile.TemporaryDirectory() as tmp:
        r = build_project(spec, used, out_root=tmp)
    ok = r['ok'] == expect_ok
    passed += ok
    print('PASS' if ok else 'FAIL', name, r['errors'])
print(passed, 'of', len(CASES), 'passed')