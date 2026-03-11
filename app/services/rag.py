import os
import glob
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_PATH = os.environ.get("CHROMA_PATH", os.path.expanduser("~/.llm-coach/chroma"))
DOCS_DIR = os.environ.get("DOCS_DIR", os.path.expanduser("~/llm-coach/docs"))

_client = None
_collection = None

def get_collection():
    global _client, _collection
    if _collection is None:
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection("docs", embedding_function=ef)
    return _collection

def index_docs():
    col = get_collection()
    md_files = glob.glob(os.path.join(DOCS_DIR, "**/*.md"), recursive=True)
    if not md_files:
        print("[RAG] 문서 없음")
        return 0
    for path in md_files:
        with open(path) as f:
            text = f.read()
        doc_id = path.replace("/", "_").replace("~", "").strip("_")
        col.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[{"path": path, "title": os.path.basename(path)}]
        )
    print(f"[RAG] {len(md_files)}개 문서 인덱싱 완료")
    return len(md_files)

def search_docs(query: str, top_k: int = 3) -> list[dict]:
    col = get_collection()
    if col.count() == 0:
        index_docs()
    results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "title": results["metadatas"][0][i].get("title", ""),
            "snippet": doc[:500],
        })
    return output
