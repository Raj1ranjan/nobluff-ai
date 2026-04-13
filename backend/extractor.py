import re


def split_sections(text):
    return re.split(r'\n(?=[A-Z][A-Za-z ]+\n)', text)


PROJECT_KEYWORDS = [
    "project", "projects", "personal projects",
    "side projects", "key projects", "academic projects"
]

TECH_SIGNALS = ["built", "developed", "implemented", "deployed", "designed"]


def is_project_section(text):
    lower = text.lower()
    if any(kw in lower for kw in PROJECT_KEYWORDS):
        return True
    # heuristic: bullet density + tech verbs
    bullets = lower.count("•") + lower.count("-")
    signals = sum(1 for s in TECH_SIGNALS if s in lower)
    return bullets >= 2 and signals >= 2


def get_projects_section(sections):
    for sec in sections:
        if is_project_section(sec):
            return sec
    return ""


def split_projects(project_text):
    projects = re.split(r'\n[-•]\s|\n(?=[A-Z][^\n]{3,50}\n)', project_text)
    return [p.strip() for p in projects if len(p.strip()) > 30]


def extract_projects(text):
    sections = split_sections(text)
    project_section = get_projects_section(sections)

    if not project_section:
        # fallback: try old regex approach
        match = re.search(r"(Projects|PROJECTS)(.*?)(Education|Experience|Skills|$)", text, re.S)
        project_section = match.group(2) if match else ""

    raw_projects = split_projects(project_section)

    projects = []
    for chunk in raw_projects:
        name = chunk.split("\n")[0].strip()
        projects.append({"name": name, "description": chunk, "tech": []})

    return projects
