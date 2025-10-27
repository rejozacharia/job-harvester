import sqlite3
from pathlib import Path
from .settings import settings

DDL = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  title TEXT,
  company TEXT,
  location TEXT,
  via TEXT,
  posted_at TEXT,
  url TEXT,
  source TEXT,
  description TEXT,
  salary TEXT,
  llm_score REAL,
  llm_blurb TEXT,
  assessment_flag INTEGER DEFAULT 0,
  assessment_terms TEXT DEFAULT '',
<<<<<<< HEAD
  status TEXT DEFAULT 'harvested',
  notes TEXT DEFAULT '',
=======
>>>>>>> main
  created_at TEXT
);
"""

MIGRATIONS = [
    ("assessment_flag", "ALTER TABLE jobs ADD COLUMN assessment_flag INTEGER DEFAULT 0"),
    ("assessment_terms", "ALTER TABLE jobs ADD COLUMN assessment_terms TEXT DEFAULT ''"),
<<<<<<< HEAD
    ("status", "ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT 'harvested'"),
    ("notes", "ALTER TABLE jobs ADD COLUMN notes TEXT DEFAULT ''"),
=======
>>>>>>> main
]

def connect():
    Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(DDL)
    # run simple column migrations
    cols = {r[1] for r in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    for col, stmt in MIGRATIONS:
        if col not in cols:
            try:
                conn.execute(stmt)
            except Exception:
                pass
    return conn
