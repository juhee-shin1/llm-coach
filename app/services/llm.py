import json
import urllib.request
from app.core.config import settings


def call_llm(system_prompt: str, user_content: str) -> dict:
    payload = json.dumps({
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "stream": False
    }).encode()

    req = urllib.request.Request(
        f"{settings.ollama_base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    text = data["message"]["content"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


HINT_SYSTEM = """
당신은 K8s SRE 튜터입니다.
아래 입력(JSON)을 보고, 반드시 아래 JSON 형식으로만 답하세요. 다른 텍스트는 절대 출력하지 마세요.

{
  "summary": "현재까지 진단 진행 상황 2~3줄",
  "next_commands": ["kubectl ...", "kubectl ..."],
  "doc_suggestions": ["관련 문서 제목1", "관련 문서 제목2"]
}
""".strip()

REPORT_SYSTEM = """
당신은 K8s SRE 튜터입니다.
세션이 끝난 뒤 학습 리뷰 리포트를 작성합니다.
반드시 아래 JSON 형식으로만 답하세요.

{
  "diagnosis_flow": "진단 흐름 평가 (1~2단락)",
  "good_points": ["좋았던 점1", "좋았던 점2"],
  "improve_points": ["개선할 점1", "개선할 점2"],
  "recommended_approach": ["권장 접근 순서1", "2", "3"],
  "reference_docs": ["문서 제목 또는 URL"]
}
""".strip()


def generate_hint(scenario_meta, recent_commands, cluster_summary, doc_snippets):
    payload = {
        "scenario": scenario_meta,
        "recent_commands": recent_commands,
        "cluster_summary": cluster_summary,
        "doc_snippets": doc_snippets,
    }
    return call_llm(HINT_SYSTEM, json.dumps(payload, ensure_ascii=False))


def generate_report(scenario_meta, all_commands, cluster_timeline, doc_list):
    payload = {
        "scenario": scenario_meta,
        "all_commands": all_commands,
        "cluster_timeline": cluster_timeline,
        "doc_list": doc_list,
    }
    return call_llm(REPORT_SYSTEM, json.dumps(payload, ensure_ascii=False))
