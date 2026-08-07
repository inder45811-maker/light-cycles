"""
Edu Mode — university class management, assignments, grade export.
.edu email verification, class creation, student tracking.
"""

import time
import secrets
import sqlite3
import csv
import io
from pathlib import Path
from dataclasses import dataclass, field

DB_PATH = Path(__file__).parent / "light_cycles.db"


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_edu_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            university TEXT NOT NULL,
            professor_id TEXT NOT NULL REFERENCES users(id),
            invite_code TEXT UNIQUE NOT NULL,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS class_students (
            class_id TEXT NOT NULL REFERENCES classes(id),
            user_id TEXT NOT NULL REFERENCES users(id),
            joined_at REAL NOT NULL,
            PRIMARY KEY (class_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            class_id TEXT NOT NULL REFERENCES classes(id),
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            test_cases_json TEXT NOT NULL DEFAULT '[]',
            mode TEXT NOT NULL DEFAULT 'battle',  -- battle, pit, debate
            due_at REAL,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id TEXT PRIMARY KEY,
            assignment_id TEXT NOT NULL REFERENCES assignments(id),
            user_id TEXT NOT NULL REFERENCES users(id),
            battle_id TEXT,
            score REAL,
            submitted_at REAL NOT NULL
        );
    """)
    db.commit()
    db.close()


# ── Class management ────────────────────────────────────────────────

def create_class(professor_id: str, name: str, university: str) -> dict:
    db = get_db()
    class_id = f"class-{secrets.token_hex(6)}"
    invite_code = f"LC-{secrets.token_hex(4).upper()}"

    db.execute("""
        INSERT INTO classes (id, name, university, professor_id, invite_code, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (class_id, name, university, professor_id, invite_code, time.time()))
    db.commit()
    db.close()
    return {"id": class_id, "name": name, "university": university, "invite_code": invite_code}


def join_class(user_id: str, invite_code: str) -> dict | None:
    db = get_db()
    cls = db.execute("SELECT * FROM classes WHERE invite_code = ?", (invite_code,)).fetchone()
    if not cls:
        db.close()
        return None

    # Check not already joined
    existing = db.execute(
        "SELECT 1 FROM class_students WHERE class_id = ? AND user_id = ?",
        (cls["id"], user_id)
    ).fetchone()
    if existing:
        db.close()
        return dict(cls)

    db.execute(
        "INSERT INTO class_students (class_id, user_id, joined_at) VALUES (?, ?, ?)",
        (cls["id"], user_id, time.time())
    )
    db.commit()
    db.close()
    return dict(cls)


def get_professor_classes(professor_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("SELECT * FROM classes WHERE professor_id = ? ORDER BY created_at DESC", (professor_id,)).fetchall()
    result = []
    for row in rows:
        cls = dict(row)
        students = db.execute("SELECT COUNT(*) as cnt FROM class_students WHERE class_id = ?", (row["id"],)).fetchone()
        cls["student_count"] = students["cnt"]
        result.append(cls)
    db.close()
    return result


def get_student_classes(user_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("""
        SELECT c.* FROM classes c
        JOIN class_students cs ON c.id = cs.class_id
        WHERE cs.user_id = ?
        ORDER BY c.created_at DESC
    """, (user_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_class_students(class_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("""
        SELECT u.username, u.email, cs.joined_at, u.id
        FROM class_students cs
        JOIN users u ON cs.user_id = u.id
        WHERE cs.class_id = ?
        ORDER BY cs.joined_at
    """, (class_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── Assignments ─────────────────────────────────────────────────────

def create_assignment(class_id: str, title: str, description: str, test_cases: list[dict], mode: str = "battle") -> dict:
    import json
    db = get_db()
    aid = f"asgn-{secrets.token_hex(6)}"

    db.execute("""
        INSERT INTO assignments (id, class_id, title, description, test_cases_json, mode, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (aid, class_id, title, description, json.dumps(test_cases), mode, time.time()))
    db.commit()
    db.close()
    return {"id": aid, "title": title, "description": description, "mode": mode}


def get_class_assignments(class_id: str) -> list[dict]:
    import json
    db = get_db()
    rows = db.execute(
        "SELECT * FROM assignments WHERE class_id = ? ORDER BY created_at DESC",
        (class_id,)
    ).fetchall()
    result = []
    for row in rows:
        a = dict(row)
        a["test_cases"] = json.loads(a["test_cases_json"])
        subs = db.execute(
            "SELECT COUNT(*) as cnt FROM assignment_submissions WHERE assignment_id = ?",
            (row["id"],)
        ).fetchone()
        a["submission_count"] = subs["cnt"]
        result.append(a)
    db.close()
    return result


def submit_assignment(assignment_id: str, user_id: str, battle_id: str, score: float = 0) -> dict:
    db = get_db()
    sid = f"sub-{secrets.token_hex(6)}"
    db.execute("""
        INSERT INTO assignment_submissions (id, assignment_id, user_id, battle_id, score, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sid, assignment_id, user_id, battle_id, score, time.time()))
    db.commit()
    db.close()
    return {"id": sid, "battle_id": battle_id, "score": score}


def get_assignment_leaderboard(assignment_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("""
        SELECT u.username, s.score, s.submitted_at, s.battle_id
        FROM assignment_submissions s
        JOIN users u ON s.user_id = u.id
        WHERE s.assignment_id = ?
        ORDER BY s.score DESC
    """, (assignment_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def export_grades_csv(class_id: str) -> str:
    """Export all student grades as CSV."""
    db = get_db()
    assignments = db.execute(
        "SELECT * FROM assignments WHERE class_id = ? ORDER BY created_at",
        (class_id,)
    ).fetchall()
    students = db.execute("""
        SELECT u.username, u.email, u.id
        FROM class_students cs JOIN users u ON cs.user_id = u.id
        WHERE cs.class_id = ? ORDER BY u.username
    """, (class_id,)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    header = ["Student", "Email"] + [a["title"] for a in assignments] + ["Average"]
    writer.writerow(header)

    for student in students:
        row = [student["username"], student["email"]]
        scores = []
        for a in assignments:
            sub = db.execute(
                "SELECT MAX(score) as best FROM assignment_submissions WHERE assignment_id = ? AND user_id = ?",
                (a["id"], student["id"])
            ).fetchone()
            score = sub["best"] if sub and sub["best"] is not None else ""
            row.append(score)
            if isinstance(score, (int, float)):
                scores.append(score)
        avg = round(sum(scores) / len(scores), 1) if scores else ""
        row.append(avg)
        writer.writerow(row)

    db.close()
    return output.getvalue()


def is_edu_email(email: str) -> bool:
    """Check if email is from an educational institution."""
    return email.lower().endswith(".edu") or ".ac." in email.lower()


# Initialize on import
init_edu_db()
