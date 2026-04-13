import json
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from pdf_parser import extract_text_from_pdf
from llm import extract_projects_llm, process_project
from database import init_db, save_resume, save_project, save_questions, get_questions_by_project, save_feedback, get_feedback, get_all_resumes, get_projects_by_resume

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
init_db()


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Free limit reached. Please wait a minute 🚀"}
    )


class FeedbackPayload(BaseModel):
    question_id: int
    rating: int
    notes: str = ""
    useful: bool = False


@app.post("/feedback")
def submit_feedback(payload: FeedbackPayload):
    save_feedback(payload.question_id, payload.rating, payload.notes, payload.useful)
    return {"status": "saved"}


@app.get("/feedback/{question_id}")
def get_feedback_endpoint(question_id: int):
    fb = get_feedback(question_id)
    return fb if fb else {}


@app.get("/resumes")
def list_resumes():
    return get_all_resumes()


@app.get("/resumes/{resume_id}/projects")
def list_projects(resume_id: int):
    return get_projects_by_resume(resume_id)


@app.get("/projects/{project_id}/questions")
def list_questions(project_id: int):
    return [dict(r) for r in get_questions_by_project(project_id)]


def _get_score(result):
    c = result.get("confidence", 0)
    return c["score"] if isinstance(c, dict) else c


def _resume_summary(results):
    if not results:
        return {}
    scores = [_get_score(r) for r in results]
    avg = int(sum(scores) / len(scores))
    high_risk = sum(1 for s in scores if s < 50)
    worst = min(results, key=_get_score)
    if avg >= 75:
        verdict = "Strong profile — projects demonstrate solid, verifiable skills"
    elif avg >= 50:
        verdict = "Decent profile — some projects need stronger technical clarity"
    else:
        verdict = "Weak profile — high bluff risk across multiple projects"
    return {
        "average_score": avg,
        "high_risk_projects": high_risk,
        "verdict": verdict,
        "most_questionable": {"name": worst.get("project_name"), "score": _get_score(worst)}
    }


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    text = extract_text_from_pdf(await file.read())
    projects = extract_projects_llm(text)
    resume_id = save_resume(file.filename)

    results = []
    for project in projects:
        result = process_project(project)
        confidence_score = _get_score(result)
        interview_questions = result.get("interview_questions", [])

        project_id = save_project(resume_id, result["project_name"], confidence_score)
        save_questions(project_id, [q.get("question", "") for q in interview_questions])
        db_questions = get_questions_by_project(project_id)

        for q, row in zip(interview_questions, db_questions):
            q["question_id"] = row["id"]

        results.append(result)

    return {"results": results, "summary": _resume_summary(results)}


@app.post("/analyze-stream")
@limiter.limit("3/minute")
async def analyze_resume_stream(request: Request, file: UploadFile = File(...)):
    file_bytes = await file.read()
    file_name = file.filename

    def generate():
        text = extract_text_from_pdf(file_bytes)
        projects = extract_projects_llm(text)

        if not projects:
            yield json.dumps({"error": "No projects found in resume"}) + "\n"
            return

        resume_id = save_resume(file_name)

        results = []
        for project in projects:
            result = process_project(project)
            confidence_score = _get_score(result)
            interview_questions = result.get("interview_questions", [])

            project_id = save_project(resume_id, result["project_name"], confidence_score)
            save_questions(project_id, [q.get("question", "") for q in interview_questions])
            db_questions = get_questions_by_project(project_id)

            for q, row in zip(interview_questions, db_questions):
                q["question_id"] = row["id"]

            results.append(result)
            yield json.dumps(result) + "\n"

        yield json.dumps({"summary": _resume_summary(results)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
