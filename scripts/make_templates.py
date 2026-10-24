import json
from pathlib import Path
T = Path('templates/standard_pattern')
DATAFLOW = '''<dataflow doc='DOC' chain='{{CHAIN}}' output='{{CHAIN}}_DOC.
{{FORMAT_EXT}}' endpoint='ftp_{{CHAIN}}'/>'''
FILES = {
'project.xml': '''<project name='{{PROJECT_NAME}}' chain='{{CHAIN}}'
ftp_owner='{{FTP_OWNER}}'/>''',
'endpoints/ftp_{{CHAIN}}.xml': '''<endpoint type='ftp'
name='ftp_{{CHAIN}}' chain='{{CHAIN}}' host_owner='{{FTP_OWNER}}'
folder='/out/{{CHAIN}}'/>''',
}
for doc in ['810', '850', '855', '997']:
    FILES['dataflows/' + doc + '_{{CHAIN}}.xml'] = DATAFLOW.replace('DOC',
doc)
for rel, text in FILES.items():
    path = T / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
Path('registry.json').write_text(json.dumps({'used_chains': ['ACM', 'XTR']}))
print('template files:', len(FILES))
