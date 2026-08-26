import sqlite3
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

DB_NAME = Path(__file__).resolve().parent.parent / "digest.db"

class Opportunity(BaseModel):
    title: str
    category: str
    organization: str
    eligibility: str
    deadline: str
    apply_url: str
    summary: str

SEED_OPPORTUNITIES = [
    Opportunity(title="MLSA Student Ambassador", category="Student Program", organization="Microsoft", eligibility="Students enrolled in an accredited institution", deadline="Rolling", apply_url="https://studentambassadors.microsoft.com/", summary="Join Microsoft's student community and build technical leadership experience. Applications open periodically by region."),
    Opportunity(title="Google Summer of Code", category="Fellowship", organization="Google", eligibility="Open source contributors aged 18 or older", deadline="Annual", apply_url="https://summerofcode.withgoogle.com/", summary="A global program that pairs contributors with open source organizations for paid project work. Explore participating organizations and project ideas."),
    Opportunity(title="GitHub Campus Experts", category="Student Program", organization="GitHub", eligibility="Students building or growing a developer community", deadline="Rolling", apply_url="https://education.github.com/experiences/campus_experts", summary="Develop community leadership skills with training, mentorship, and resources from GitHub. Applications are accepted in program cohorts."),
    Opportunity(title="LFX Mentorship", category="Fellowship", organization="Linux Foundation", eligibility="Developers and students interested in open source", deadline="Multiple cohorts", apply_url="https://mentorship.lfx.linuxfoundation.org/", summary="Work with leading open source projects under an experienced mentor. Browse current terms, projects, and stipend details on the portal."),
]


def init_db() -> None:
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                category TEXT,
                organization TEXT,
                eligibility TEXT,
                deadline TEXT,
                apply_url TEXT UNIQUE,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.executemany("""
            INSERT OR IGNORE INTO opportunities
            (title, category, organization, eligibility, deadline, apply_url, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [tuple(item.model_dump().values()) for item in SEED_OPPORTUNITIES])

def insert_opportunity(opp: Opportunity):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO opportunities
            (title, category, organization, eligibility, deadline, apply_url, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (opp.title, opp.category, opp.organization, opp.eligibility, opp.deadline, opp.apply_url, opp.summary))
        return conn.total_changes > 0

def fetch_all_opportunities(category: Optional[str] = None) -> List[dict]:
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM opportunities WHERE category = ? ORDER BY id DESC", (category,))
        else:
            cursor.execute("SELECT * FROM opportunities ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]