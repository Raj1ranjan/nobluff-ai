def normalize_question(q):
    if isinstance(q, str):
        return q.strip()
    if isinstance(q, dict):
        val = q.get("question", "")
        return val.strip() if isinstance(val, str) else ""
    return ""
