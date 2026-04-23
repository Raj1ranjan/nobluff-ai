import os
import sqlite3
from utils import normalize_question

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nobluff.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER,
        name TEXT,
        confidence INTEGER,
        FOREIGN KEY (resume_id) REFERENCES resumes(id)
    );
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        question_text TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER UNIQUE,
        rating INTEGER,
        notes TEXT,
        useful BOOLEAN,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)
    conn.commit()
    conn.close()


def save_resume(file_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO resumes (file_name) VALUES (?)", (file_name,))
    conn.commit()
    resume_id = cur.lastrowid
    conn.close()
    return resume_id


def save_project(resume_id, name, confidence):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (resume_id, name, confidence) VALUES (?, ?, ?)",
        (resume_id, name, confidence)
    )
    conn.commit()
    project_id = cur.lastrowid
    conn.close()
    return project_id


def save_questions(project_id, questions):
    conn = get_connection()
    cur = conn.cursor()
    for q in questions:
        cur.execute(
            "INSERT INTO questions (project_id, question_text) VALUES (?, ?)",
            (project_id, normalize_question(q))
        )
    conn.commit()
    conn.close()


def get_questions_by_project(project_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE project_id=?", (project_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_feedback(question_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM feedback WHERE question_id=?", (question_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_resumes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, file_name, uploaded_at FROM resumes ORDER BY uploaded_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_projects_by_resume(resume_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, confidence FROM projects WHERE resume_id=?", (resume_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_feedback(question_id, rating, notes, useful):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO feedback (question_id, rating, notes, useful) VALUES (?, ?, ?, ?)
           ON CONFLICT(question_id) DO UPDATE SET rating=excluded.rating,
           notes=excluded.notes, useful=excluded.useful""",
        (question_id, rating, notes, useful)
    )
    conn.commit()
    conn.close()
