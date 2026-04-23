import requests
import os
import json
import re
from dotenv import load_dotenv
from prompts import EXTRACT_PROJECT_PROMPT, ANALYZE_PROJECT_PROMPT, GLOBAL_ANALYSIS_PROMPT
from utils import normalize_question

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq_raw(system_prompt, user_content) -> str:
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.1-8b-instant",
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        },
        timeout=30
    )
    return response.json()["choices"][0]["message"]["content"]


def _call_groq(system_prompt, user_content):
    content = _call_groq_raw(system_prompt, user_content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        clean = re.sub(r"```(?:json)?|```", "", content).strip()
        return json.loads(clean)


def safe_json_load(response_text):
    try:
        return json.loads(response_text)
    except Exception:
        try:
            clean = re.sub(r"```(?:json)?|```", "", response_text).strip()
            return json.loads(clean)
        except Exception:
            return []


def validate_projects(projects) -> list:
    valid = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        name = p.get("name", "").strip()
        desc = p.get("description", "").strip()
        if not name or not desc:
            continue
        valid.append({
            "name": name,
            "description": desc,
            "tech_stack": p.get("tech_stack", []),
            "claims": p.get("claims", [])
        })
    return valid


def extract_projects_llm(resume_text: str) -> list:
    try:
        raw = _call_groq_raw(EXTRACT_PROJECT_PROMPT, resume_text)
        parsed = safe_json_load(raw)
        return validate_projects(parsed)
    except Exception:
        return []


def clean_questions(questions: list) -> list:
    seen = set()
    unique = []
    for q in questions:
        key = (q.get("question", "") if isinstance(q, dict) else q).strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(q)
    return sorted(unique, key=lambda q: q.get("priority", 99))


def generate_verdict(score: int) -> str:
    if score >= 75:
        return "Strong project — likely genuine with solid implementation depth"
    elif score >= 50:
        return "Moderate confidence — some claims need verification"
    else:
        return "High bluff risk — lacks clear technical depth and detail"


def confidence_label(score: int) -> str:
    if score >= 85:
        return "Strong"
    elif score >= 70:
        return "Needs polish"
    else:
        return "At risk"


def process_project(project: dict) -> dict:
    prompt = ANALYZE_PROJECT_PROMPT.format(
        name=project.get("name", ""),
        description=project.get("description", ""),
        tech_stack=", ".join(project.get("tech_stack", [])),
        claims="\n".join(project.get("claims", []))
    )
    try:
        result = _call_groq("You are a senior software engineer.", prompt)
    except Exception as e:
        return {
            "project_name": project.get("name", "Unknown"),
            "tech_stack": project.get("tech_stack", []),
            "confidence": {"score": 0, "reason": str(e)},
            "verdict": generate_verdict(0),
            "weak_spots": [],
            "trap_questions": [],
            "improvements": [],
            "interview_questions": []
        }

    score = max(0, min(100, int(result.get("readiness_score", 50))))
    raw_weak_spots = result.get("weak_spots", [])

    # normalise weak_spots — accept both string and {point, severity} formats
    weak_spots = []
    for w in raw_weak_spots:
        if isinstance(w, dict):
            weak_spots.append({
                "point": w.get("point", ""),
                "severity": w.get("severity", "medium"),
                "fix_strategy": w.get("fix_strategy", [])
            })
        else:
            weak_spots.append({"point": str(w), "severity": "medium", "fix_strategy": []})

    severity_order = {"high": 0, "medium": 1, "low": 2}
    weak_spots.sort(key=lambda w: severity_order.get(w["severity"], 1))

    penalty = sum(3 if w["severity"] == "high" else 2 if w["severity"] == "medium" else 1 for w in weak_spots)
    base_score = score
    final_score = max(0, base_score - penalty)

    # normalise trap_questions — add severity + priority if missing
    raw_traps = result.get("trap_questions", [])
    trap_questions = sorted(
        [
            {
                "weak_spot": t.get("weak_spot", ""),
                "severity": t.get("severity", "medium"),
                "trap_question": t.get("trap_question", ""),
                "why_it_exposes_you": t.get("why_it_exposes_you", ""),
                "priority": t.get("priority", 99)
            }
            for t in raw_traps if isinstance(t, dict)
        ],
        key=lambda t: t["priority"]
    )

    questions = clean_questions(result.get("questions", []))

    return {
        "project_name": project.get("name"),
        "tech_stack": project.get("tech_stack", []),
        "confidence": {
            "score": final_score,
            "base_score": base_score,
            "penalty": penalty,
            "label": confidence_label(final_score),
            "reason": result.get("readiness_reason", "")
        },
        "verdict": generate_verdict(final_score),
        "weak_spots": weak_spots,
        "trap_questions": trap_questions,
        "improvements": result.get("improvements", []),
        "interview_questions": [
            {
                "question": normalize_question(q.get("question", "")),
                "answer": q.get("answer", ""),
                "difficulty": q.get("difficulty", "medium"),
                "priority": q.get("priority", 99),
                "why_asked": q.get("why_asked", ""),
                "expected_signals": q.get("expected_signals", ""),
                "red_flags": q.get("red_flags", "")
            }
            for q in questions
        ]
    }


def generate_global_analysis(results: list) -> dict:
    projects_json = json.dumps([
        {
            "name": r["project_name"],
            "readiness_score": r["confidence"]["score"] if isinstance(r["confidence"], dict) else r["confidence"],
            "weak_spots": r.get("weak_spots", []),
            "top_questions": [q["question"] for q in r.get("interview_questions", [])[:2]]
        }
        for r in results
    ])
    try:
        return _call_groq("You are a senior software engineer.", GLOBAL_ANALYSIS_PROMPT.format(projects_json=projects_json))
    except Exception:
        return {}
