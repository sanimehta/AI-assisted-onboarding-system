import json
from pathlib import Path
import chromadb
import ollama

EMBED = 'nomic-embed-text'

def _col():
    db = chromadb.PersistentClient(path='chroma_db')
    return db.get_or_create_collection('library', metadata={'hnsw:space': 'cosine'})

def build_library(emails):
    ids, docs, metas = [], [], []
    for path in sorted(Path('data/library').glob('*.md')):
        for j, sec in enumerate(path.read_text().split('## ')[1:]):
            ids.append(path.stem + '-' + str(j))
            docs.append(sec.strip())
            metas.append({'ref': path.name, 'kind': 'glossary'})
    for e in emails:
        ids.append('email-' + e['id'])
        docs.append(e['text'] + ' => ' + json.dumps(e['gold']))
        metas.append({'ref': e['id'], 'kind': 'example'})
    vectors = ollama.embed(model=EMBED, input=docs).embeddings
    _col().upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vectors)

def retrieve(query, exclude_id=None, k_glossary=3, k_examples=2):
    vec = ollama.embed(model=EMBED, input=[query]).embeddings
    col = _col()
    gl = col.query(query_embeddings=vec, n_results=k_glossary, where={'kind': 'glossary'})
    ex = col.query(query_embeddings=vec, n_results=k_examples + 1, where={'kind': 'example'})
    out = list(gl['documents'][0])
    out += [d for d, m in zip(ex['documents'][0], ex['metadatas'][0]) if m['ref'] != exclude_id][:k_examples]
    return out