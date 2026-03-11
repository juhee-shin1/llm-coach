import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection
from app.services.scenario import apply_scenario, delete_scenario, get_scenario_meta

router = APIRouter()

class StartRequest(BaseModel):
    scenario_id: str

class FinishRequest(BaseModel):
    session_id: str

@router.post("/start")
def start_session(req: StartRequest):
    meta = get_scenario_meta(req.scenario_id)
    if not meta:
        raise HTTPException(404, f"Scenario '{req.scenario_id}' not found")
    ok, output = apply_scenario(req.scenario_id)
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    conn.execute("INSERT INTO sessions(id,scenario_id,started_at,status) VALUES(?,?,?,?)",
                 (session_id, req.scenario_id, now, "IN_PROGRESS"))
    conn.commit(); conn.close()
    return {"session_id": session_id, "scenario_title": meta.get("title"),
            "apply_ok": ok, "apply_output": output,
            "hint": f"export SESSION_ID={session_id}"}

@router.post("/finish")
def finish_session(req: FinishRequest):
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (req.session_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Session not found")
    conn.execute("UPDATE sessions SET finished_at=?,status='FINISHED' WHERE id=?",
                 (datetime.now(timezone.utc).isoformat(), req.session_id))
    conn.commit(); conn.close()
    delete_scenario(row["scenario_id"])
    return {"session_id": req.session_id, "status": "FINISHED"}

@router.get("/{session_id}")
def get_session(session_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Session not found")
    return dict(row)
