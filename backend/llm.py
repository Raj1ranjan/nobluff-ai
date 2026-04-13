import requests
import os
import json
import re
from dotenv import load_dotenv
from prompts import EXTRACT_PROJECT_PROMPT, QUESTION_PROMPT, SUSPICIOUS_PROMPT, IMPROVEMENT_PROMPT, CONFIDENCE_PROMPT
from utils import normalize_question

load_dotenv()
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


def compute_confidence(project: dict) -> dict:
    prompt = CONFIDENCE_PROMPT.format(
        name=project.get("name", ""),
        description=project.get("description", ""),
        tech_stack=", ".join(project.get("tech_stack", [])),
        claims="\n".join(project.get("claims", []))
    )
    try:
        result = _call_groq("You are a senior software engineer.", prompt)
        score = max(0, min(100, int(result.get("score", 50))))
        return {"score": score, "reason": result.get("reason", "")}
    except Exception:
        return {"score": 50, "reason": "Could not evaluate confidence."}


def generate_questions(project: dict, suspicious_points: list = []) -> list:
    prompt = QUESTION_PROMPT.format(
        name=project.get("name", ""),
        description=project.get("description", ""),
        tech_stack=", ".join(project.get("tech_stack", [])),
        claims="\n".join(project.get("claims", [])),
        suspicious_points="\n".join(suspicious_points)
    )
    try:
        result = _call_groq("You are a senior software engineer.", prompt)
        return result.get("questions", [])
    except Exception:
        return []


def generate_suspicious_points(project: dict) -> list:
    prompt = SUSPICIOUS_PROMPT.format(
        name=project.get("name", ""),
        description=project.get("description", ""),
        claims="\n".join(project.get("claims", []))
    )
    try:
        result = _call_groq("You are a senior software engineer.", prompt)
        return result.get("suspicious_points", [])
    except Exception:
        return []


def generate_improvements(project: dict, suspicious_points: list = []) -> list:
    prompt = IMPROVEMENT_PROMPT.format(
        name=project.get("name", ""),
        description=project.get("description", ""),
        tech_stack=", ".join(project.get("tech_stack", [])),
        claims="\n".join(project.get("claims", [])),
        suspicious_points="\n".join(suspicious_points)
    )
    try:
        result = _call_groq("You are a senior software engineer.", prompt)
        return result.get("improvements", [])
    except Exception:
        return []


def generate_verdict(score: int) -> str:
    if score >= 75:
        return "Strong project — likely genuine with solid implementation depth"
    elif score >= 50:
        return "Moderate confidence — some claims need verification"
    else:
        return "High bluff risk — lacks clear technical depth and detail"


def process_project(project: dict) -> dict:
    confidence = compute_confidence(project)
    suspicious_points = generate_suspicious_points(project)
    questions = generate_questions(project, suspicious_points)
    improvements = generate_improvements(project, suspicious_points)

    score = confidence["score"] if isinstance(confidence, dict) else confidence
    score = max(0, score - len(suspicious_points) * 5)
    if isinstance(confidence, dict):
        confidence["score"] = score

    return {
        "project_name": project.get("name"),
        "tech_stack": project.get("tech_stack", []),
        "confidence": confidence,
        "verdict": generate_verdict(score),
        "suspicious_points": suspicious_points,
        "improvements": improvements,
        "interview_questions": [
            {
                "question": normalize_question(q.get("question", q) if isinstance(q, dict) else q),
                "expected_signals": q.get("expected_signals", "") if isinstance(q, dict) else "",
                "red_flags": q.get("red_flags", "") if isinstance(q, dict) else ""
            }
            for q in questions
        ]
    }


def _fallback(project: dict, reason: str) -> dict:
    return {
        "project_name": project.get("name", "Unknown Project"),
        "tech_stack": [],
        "confidence": {"score": 0, "breakdown": {"clarity": 0, "tech_depth": 0, "claims": 0}},
        "suspicious_points": [f"Analysis failed: {reason}"],
        "interview_questions": [
            {"question": "Could not generate questions.", "expected_signals": "", "red_flags": reason}
        ]
    }
