#!/usr/bin/env python3
"""
Snapshotter: 20초마다 클러스터 상태를 수집해서 DB에 저장
사용법: python3 snapshotter.py
"""
import os, time, subprocess, sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/.llm-coach/db.sqlite"))
INTERVAL = int(os.environ.get("SNAPSHOT_INTERVAL_SEC", "20"))


def get_active_sessions():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id FROM sessions WHERE status='IN_PROGRESS'").fetchall()
    conn.close()
    return [r[0] for r in rows]


def collect_summary() -> str:
    lines = []
    try:
        out = subprocess.check_output(
            ["kubectl", "get", "pods", "-A", "--no-headers"], text=True, timeout=10)
        bad = [l for l in out.splitlines()
               if any(s in l for s in ["Error","BackOff","Pending","CrashLoop","OOMKilled"])]
        lines.append(f"[Pods] total={len(out.splitlines())}, abnormal={len(bad)}")
        if bad:
            lines.append("  비정상 pods: " + ", ".join(l.split()[1] for l in bad[:5]))
    except Exception as e:
        lines.append(f"[Pods] 수집 실패: {e}")

    try:
        out = subprocess.check_output(
            ["kubectl", "get", "events", "-A",
             "--field-selector", "type!=Normal",
             "--sort-by=.lastTimestamp"], text=True, timeout=10)
        warn_lines = out.strip().splitlines()[1:4]
        if warn_lines:
            lines.append("[Events] 최근 Warning:")
            lines.extend("  " + l for l in warn_lines)
    except Exception as e:
        lines.append(f"[Events] 수집 실패: {e}")

    return "\n".join(lines)


def save_snapshot(session_id: str, summary: str):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO snapshots(session_id, ts, summary) VALUES(?,?,?)",
        (session_id, now, summary))
    conn.commit()
    conn.close()


def main():
    print(f"[Snapshotter] 시작 (interval={INTERVAL}s, db={DB_PATH})")
    while True:
        sessions = get_active_sessions()
        if sessions:
            summary = collect_summary()
            for sid in sessions:
                save_snapshot(sid, summary)
                print(f"[Snapshotter] {sid} 저장 완료: {summary[:60]}...")
        else:
            print("[Snapshotter] 활성 세션 없음")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
