from pydantic import BaseModel
from typing import Optional

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str = ""
    via: str = ""
    posted_at: str = ""  # ISO date
    url: str
    source: str  # google_jobs|linkedin
    description: str = ""
    salary: str = ""
    llm_score: Optional[float] = None
    llm_blurb: Optional[str] = None
    assessment_flag: int = 0
    assessment_terms: str = ""
<<<<<<< HEAD
    status: str = "harvested"
    notes: str = ""
=======
>>>>>>> main
