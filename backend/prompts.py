EXTRACT_PROJECT_PROMPT = """
You are an expert technical interviewer.

Extract ALL projects from the resume.

Return ONLY valid JSON in this format:
[
  {
    "name": "project name",
    "description": "what the project does (clear and specific)",
    "tech_stack": ["list", "of", "technologies"],
    "claims": [
      "specific technical claims made by the candidate",
      "focus on implementation, not generic statements"
    ]
  }
]

Rules:
- Do NOT return anything except JSON
- Do NOT explain
- Be strict and precise
- If unclear, infer conservatively
"""

ANALYZE_PROJECT_PROMPT = """
You are a senior software engineer conducting a real technical interview.

Analyze this project:
Name: {name}
Description: {description}
Tech Stack: {tech_stack}
Claims: {claims}

Return ONLY valid JSON in exactly this format:
{{
  "readiness_score": <integer 0-100>,
  "readiness_reason": "<one sentence explaining the score>",
  "weak_spots": [
    {{
      "point": "weak or vague claim an interviewer will target",
      "severity": "high|medium|low",
      "fix_strategy": ["actionable step 1 to fix this weak spot", "actionable step 2"]
    }}
  ],
  "improvements": [
    "specific suggestion to make this project more credible"
  ],
  "questions": [
    {{
      "question": "hard technical question targeting a weak spot",
      "answer": "strong sample answer a genuine implementer would give",
      "difficulty": "easy|medium|hard",
      "priority": <integer 1-3, 1 = most important>,
      "why_asked": "what this question tests",
      "expected_signals": "what a genuine implementer would say",
      "red_flags": "what a bluffer would say"
    }}
  ],
  "trap_questions": [
    {{
      "weak_spot": "the weak spot this targets",
      "severity": "high|medium|low",
      "trap_question": "the exact question an interviewer would ask to expose this",
      "why_it_exposes_you": "why a bluffer would fail this",
      "priority": <integer 1-3, 1 = most dangerous>
    }}
  ]
}}

Rules:
- readiness_score: based on technical depth, specificity, clarity, evidence of real implementation
- weak_spots: 2-4 items ordered by severity (high first); fix_strategy: 2-3 concrete actionable steps for each
- improvements: 2-3 specific suggestions
- questions: exactly 3, ordered by priority ascending (1 = ask first)
- trap_questions: one per weak_spot, max 3, ordered by priority ascending
- Do NOT return anything except JSON
"""

GLOBAL_ANALYSIS_PROMPT = """
You are a senior software engineer who has just reviewed all projects on a candidate's resume.

Projects data:
{projects_json}

Return ONLY valid JSON:
{{
  "overall_readiness": <integer 0-100>,
  "biggest_risks": [
    "cross-project pattern that will hurt this candidate in interviews"
  ],
  "strongest_areas": [
    "genuine strength visible across projects"
  ],
  "likely_interview_focus": [
    "topic or area the interviewer will probe hardest based on this resume"
  ],
  "verdict": "<one sentence overall assessment>"
}}

Rules:
- biggest_risks: 2-3 items, cross-project patterns not single-project issues
- strongest_areas: 1-3 items, only genuine strengths
- likely_interview_focus: 2-3 specific topics
- Do NOT return anything except JSON
"""
