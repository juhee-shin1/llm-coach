from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection

router = APIRouter()

class CommandLogRequest(BaseModel):
    session_id: str
    command: str
    output_head: str = ""
    exit_code: int = 0

@router.post("/log")
def log_command(req: CommandLogRequest):
    conn = get_connection()
    row = conn.execute("SELECT id FROM sessions WHERE id=? AND status='IN_PROGRESS'",
                       (req.session_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Active session not found")
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("INSERT INTO commands(session_id,ts,command,output_head,exit_code) VALUES(?,?,?,?,?)",
                 (req.session_id, now, req.command, req.output_head[:2000], req.exit_code))
    conn.commit(); conn.close()
    return {"ok": True}

@router.get("/{session_id}")
def get_commands(session_id: str, limit: int = 20):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM commands WHERE session_id=? ORDER BY ts DESC LIMIT ?",
                        (session_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
