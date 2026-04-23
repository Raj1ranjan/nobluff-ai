import json
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.pdf_parser import extract_text_from_pdf
from backend.llm import extract_projects_llm, process_project, generate_global_analysis
from backend.database import init_db, save_resume, save_project, save_questions, get_questions_by_project, save_feedback, get_feedback, get_all_resumes, get_projects_by_resume

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
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


def _build_attack_plan(results, global_analysis):
    """Build a prioritised action plan purely from structured data — no LLM call."""
    # top high-severity weak spot across all projects
    all_high = [
        (w["point"], r["project_name"])
        for r in results
        for w in r.get("weak_spots", [])
        if isinstance(w, dict) and w.get("severity") == "high"
    ]
    # top priority question across all projects
    all_questions = sorted(
        [q for r in results for q in r.get("interview_questions", [])],
        key=lambda q: q.get("priority", 99)
    )
    # most dangerous trap question (priority=1)
    all_traps = sorted(
        [t for r in results for t in r.get("trap_questions", [])],
        key=lambda t: t.get("priority", 99)
    )

    fix_first = f"[High] {all_high[0][0]} (in {all_high[0][1]})" if all_high else None
    prepare_question = all_questions[0]["question"] if all_questions else None
    biggest_risk = global_analysis.get("biggest_risks", [None])[0] if global_analysis else None

    # estimate readiness after fixing high-severity issues
    avg = int(sum(_get_score(r) for r in results) / len(results)) if results else 0
    high_count = len(all_high)
    estimated_after = min(100, avg + high_count * 3)

    return {
        "fix_first": fix_first,
        "prepare_question": prepare_question,
        "biggest_risk": biggest_risk,
        "estimated_readiness_after_fix": estimated_after,
        "time_to_fix": {
            "weak_spot_fix": "30–45 mins" if high_count > 0 else "15–20 mins",
            "question_prep": f"{len(all_questions) * 15} mins"
        }
    }


def _get_score(result):
    c = result.get("confidence", 0)
    return c["score"] if isinstance(c, dict) else c


def _resume_summary(results, global_analysis=None):
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
    summary = {
        "average_score": avg,
        "high_risk_projects": high_risk,
        "verdict": verdict,
        "most_questionable": {"name": worst.get("project_name"), "score": _get_score(worst)},
        "attack_plan": _build_attack_plan(results, global_analysis)
    }
    if global_analysis:
        summary["global_analysis"] = global_analysis
    return summary


@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Invalid file type")
    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large")
    text = extract_text_from_pdf(file_bytes)
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

    global_analysis = generate_global_analysis(results)
    return {"results": results, "summary": _resume_summary(results, global_analysis)}


@app.post("/analyze-stream")
@limiter.limit("3/minute")
async def analyze_resume_stream(request: Request, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Invalid file type")
    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large")
    file_name = file.filename

    async def generate():
        import asyncio
        loop = asyncio.get_running_loop()
        try:
            text = await loop.run_in_executor(None, extract_text_from_pdf, file_bytes)
            projects = await loop.run_in_executor(None, extract_projects_llm, text)

            if not projects:
                yield json.dumps({"error": "No projects found in resume"}) + "\n"
                return

            resume_id = save_resume(file_name)

            results = []
            for project in projects:
                try:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, process_project, project),
                        timeout=45
                    )
                except asyncio.TimeoutError:
                    yield json.dumps({"error": f"Project '{project.get('name', 'unknown')}' timed out"}) + "\n"
                    continue
                except Exception as e:
                    yield json.dumps({"error": f"Failed to process project '{project.get('name', 'unknown')}': {str(e)}"}) + "\n"
                    continue

                confidence_score = _get_score(result)
                interview_questions = result.get("interview_questions", [])

                project_id = save_project(resume_id, result["project_name"], confidence_score)
                save_questions(project_id, [q.get("question", "") for q in interview_questions])
                db_questions = get_questions_by_project(project_id)

                for q, row in zip(interview_questions, db_questions):
                    q["question_id"] = row["id"]

                results.append(result)
                yield json.dumps(result) + "\n"

            global_analysis = await loop.run_in_executor(None, generate_global_analysis, results)
            yield json.dumps({"summary": _resume_summary(results, global_analysis)}) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
