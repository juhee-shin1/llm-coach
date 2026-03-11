from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection
from app.services.llm import generate_hint, generate_report
from app.services.scenario import get_scenario_meta
from app.services.rag import search_docs

router = APIRouter()


class HintRequest(BaseModel):
    session_id: str
    cluster_summary: str = ""
    doc_snippets: list[str] = []


class ReportRequest(BaseModel):
    session_id: str
    doc_list: list[str] = []


@router.post("/hint")
def get_hint(req: HintRequest):
    conn = get_connection()
    session = conn.execute("SELECT * FROM sessions WHERE id=?", (req.session_id,)).fetchone()
    if not session:
        raise HTTPException(404, "Session not found")
    rows = conn.execute(
        "SELECT command,output_head,exit_code,ts FROM commands WHERE session_id=? ORDER BY ts DESC LIMIT 10",
        (req.session_id,)).fetchall()
    conn.close()

    recent = [{"cmd": r["command"], "out": r["output_head"], "exit": r["exit_code"]} for r in rows]
    meta = get_scenario_meta(session["scenario_id"]) or {}

    query = " ".join(meta.get("related_tags", [])) + " " + req.cluster_summary
    rag_docs = search_docs(query, top_k=3)
    doc_snippets = [f"[{d['title']}]\n{d['snippet']}" for d in rag_docs]

    return generate_hint(meta, recent, req.cluster_summary, doc_snippets)


@router.post("/report")
def get_report(req: ReportRequest):
    conn = get_connection()
    session = conn.execute("SELECT * FROM sessions WHERE id=?", (req.session_id,)).fetchone()
    if not session:
        raise HTTPException(404, "Session not found")
    rows = conn.execute(
        "SELECT command,output_head,exit_code,ts FROM commands WHERE session_id=? ORDER BY ts ASC",
        (req.session_id,)).fetchall()
    snaps = conn.execute(
        "SELECT summary,ts FROM snapshots WHERE session_id=? ORDER BY ts ASC",
        (req.session_id,)).fetchall()
    conn.close()

    all_cmds = [{"cmd": r["command"], "out": r["output_head"], "exit": r["exit_code"]} for r in rows]
    timeline = [{"ts": s["ts"], "summary": s["summary"]} for s in snaps]
    meta = get_scenario_meta(session["scenario_id"]) or {}

    query = " ".join(meta.get("related_tags", []))
    rag_docs = search_docs(query, top_k=3)
    doc_list = [d["title"] for d in rag_docs]

    return generate_report(meta, all_cmds, timeline, doc_list)
