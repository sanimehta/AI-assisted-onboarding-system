from pathlib import Path
from mcp_server import check_spec, suggest_chain, preview_project

GOOD = {'chain': 'ZEP', 'docs': ['850', '810'], 'format': 'xml',
        'ftp_owner': 'us', 'project_name': 'zephyr_foods'}

def test_good_spec_is_valid():
    assert check_spec(GOOD) == {'errors': []}

def test_preview_builds_expected_files():
    before = Path('registry.json').read_text()
    r = preview_project(GOOD)
    assert r['ok'] is True
    assert sorted(r['files']) == ['dataflows/810_ZEP.xml', 'dataflows/850_ZEP.xml',
                                  'endpoints/ftp_ZEP.xml', 'project.xml']
    assert not Path('projects/zephyr_foods').exists()      # nothing was saved
    assert Path('registry.json').read_text() == before     # chain was not reserved

def test_bad_specs_are_rejected():
    assert check_spec(dict(GOOD, chain='zep'))['errors']           # lowercase
    assert check_spec(dict(GOOD, chain='ACM'))['errors']           # already used
    assert check_spec(dict(GOOD, docs=['810', '999']))['errors']   # unsupported doc

def test_suggest_chain_is_valid():
    chain = suggest_chain('Zephyr Foods')['chain']
    assert chain and 3 <= len(chain) <= 5 and chain.isupper()

if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('PASS', name)