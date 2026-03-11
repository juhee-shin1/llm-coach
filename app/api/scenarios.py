from fastapi import APIRouter
from app.services.scenario import list_scenarios, get_scenario_meta

router = APIRouter()

@router.get("/")
def list_all():
    return list_scenarios()

@router.get("/{scenario_id}")
def get_one(scenario_id: str):
    meta = get_scenario_meta(scenario_id)
    return meta or {"error": "not found"}


from fastapi import APIRouter as _AR
from app.services.rag import index_docs, search_docs

@router.post("/rag/index")
def rag_index():
    count = index_docs()
    return {"indexed": count}

@router.get("/rag/search")
def rag_search(q: str, top_k: int = 3):
    return search_docs(q, top_k)
