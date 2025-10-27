from typing import Dict, Any, List
from datetime import datetime
from rich import print as rprint
from rich.table import Table
from .settings import settings
from .models import Job
from .sources import SerpGoogleJobs, SerpLinkedInJobs
from .agent import LLMScorer, detect_assessment
from .scrape import fetch_full_description
from .db import connect
import csv

class Store:
    def __init__(self):
        self.conn = connect()

    def upsert(self, job: Job) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM jobs WHERE id=?", (job.id,))
        if cur.fetchone():
            return False
        status = (job.status or "").strip().lower()
        choices = settings.JOB_STATUS_CHOICES
        if choices:
            if status not in choices:
                status = choices[0]
        elif not status:
            status = "harvested"
        notes = (job.notes or "").strip()
        job.status = status
        job.notes = notes
        cur.execute(
            """
            INSERT INTO jobs(id,title,company,location,via,posted_at,url,source,description,salary,
                             llm_score,llm_blurb,assessment_flag,assessment_terms,status,notes,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job.id, job.title, job.company, job.location, job.via, job.posted_at, job.url, job.source,
                job.description, job.salary, job.llm_score, job.llm_blurb, job.assessment_flag, job.assessment_terms,
                status, notes,
                datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()
        return True

    def latest(self, limit: int = 20) -> List[Job]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id,title,company,location,via,posted_at,url,source,description,salary,llm_score,llm_blurb,assessment_flag,assessment_terms,status,notes FROM jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        default_status = None
        if settings.JOB_STATUS_CHOICES:
            default_status = settings.JOB_STATUS_CHOICES[0]
        return [Job(
            id=r[0], title=r[1], company=r[2], location=r[3], via=r[4], posted_at=r[5], url=r[6], source=r[7],
            description=r[8], salary=r[9], llm_score=r[10], llm_blurb=r[11], assessment_flag=r[12], assessment_terms=r[13],
            status=(r[14] or default_status or "harvested"), notes=(r[15] or "")
        ) for r in rows]

    def update_status(self, job_id: str, status: str, notes: str | None = None) -> bool:
        if settings.JOB_STATUS_CHOICES and status not in settings.JOB_STATUS_CHOICES:
            raise ValueError("invalid status")
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,))
        if not cur.fetchone():
            return False
        cur.execute(
            "UPDATE jobs SET status=?, notes=? WHERE id=?",
            (status, notes or "", job_id),
        )
        self.conn.commit()
        return True

class Exporter:
    @staticmethod
    def export_csv(jobs: List[Job], outdir: str) -> str | None:
        if not jobs:
            return None
        import os
        os.makedirs(outdir, exist_ok=True)
        fname = f"{outdir}/jobs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "title","company","location","url","source","via","posted_at","salary",
                "llm_score","llm_blurb","assessment_flag","assessment_terms","status","notes","description"
            ])
            for j in jobs:
                w.writerow([
                    j.title, j.company, j.location, j.url, j.source, j.via, j.posted_at, j.salary,
                    j.llm_score or "", j.llm_blurb or "", j.assessment_flag, j.assessment_terms, j.status, j.notes, j.description
                ])
        return fname

class Runner:
    def __init__(self):
        self.store = Store()
        self.llm = LLMScorer()

    def _queries(self) -> list[str]:
        extras = f" {' '.join(settings.QUERY_KEYWORDS)}" if settings.QUERY_KEYWORDS else ""
        return [f"{t}{extras}".strip() for t in (settings.QUERY_TITLES or [])]

    def _is_senior(self, title: str) -> bool:
        tl = title.lower()
        return any(k in tl for k in ["chief","vp","director","head","lead","principal"]) and not any(k in tl for k in ["intern","junior","entry"])

    def run_once(self) -> Dict[str, Any]:
        all_new: list[Job] = []
        for location in (settings.LOCATIONS or ["Remote"]):
            for q in self._queries():
                rprint(f"[bold]Searching[/bold] q='{q}' in '{location}' REMOTE_ONLY={settings.REMOTE_ONLY}")
                gj = SerpGoogleJobs.search(q, location, settings.REMOTE_ONLY, settings.MAX_RESULTS)
                lj = SerpLinkedInJobs.search(q, location, settings.REMOTE_ONLY, max(0, settings.MAX_RESULTS//2))
                for job in gj + lj:
                    if not self._is_senior(job.title):
                        continue
                    full_text = fetch_full_description(job.url)
                    if full_text:
                        job.description = (full_text + "\n\n---\nSERP snippet:\n" + (job.description or ""))[:20000]
                    flag, terms = detect_assessment(job.description or "")
                    job.assessment_flag, job.assessment_terms = flag, terms
                    if settings.ENABLE_ASSESSMENT_FILTER and not job.assessment_flag:
                        continue
                    job = self.llm.score_and_blurb(job)
                    if settings.ENABLE_ASSESSMENT_BOOST and job.assessment_flag:
                        job.llm_score = min((job.llm_score or 0) + settings.ASSESSMENT_SCORE_BOOST, 100.0)
                    inserted = self.store.upsert(job)
                    if inserted:
                        all_new.append(job)
        csv_path = Exporter.export_csv(all_new, settings.OUTPUT_DIR)
        self._print_table(all_new)
        return {"inserted": len(all_new), "csv": csv_path}

    def _print_table(self, jobs: list[Job]):
        if not jobs:
            rprint("[yellow]No new matches this run.[/yellow]")
            return
        table = Table(title=f"New matches ({len(jobs)})")
        table.add_column("Score", justify="right", no_wrap=True)
        table.add_column("Assess", justify="center", no_wrap=True)
        table.add_column("Title")
        table.add_column("Company")
        table.add_column("Loc")
        table.add_column("Source", no_wrap=True)
        table.add_column("Posted")
        for j in sorted(jobs, key=lambda x: (x.llm_score or 0), reverse=True)[:20]:
            table.add_row(str(int(j.llm_score or 0)), "✓" if j.assessment_flag else "", j.title, j.company, j.location, j.source, (j.posted_at or "")[:10])
        rprint(table)
