from onboard.generate import build_project, load_used

spec = {'project_name': 'NewCo_Foods', 'chain': 'NCF', 'docs': ['810', '855'],
        'format': 'xml', 'ftp_owner': 'customer'}
print(build_project(spec, load_used())) 