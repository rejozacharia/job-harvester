import json
import re
from typing import Tuple
from .models import Job
from .settings import settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

class LLMScorer:
    def __init__(self):
        self.enabled = False
        self.client = None
        self.model = settings.LLM_MODEL
        if settings.OPENAI_API_KEY and OpenAI:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.enabled = True
        elif settings.OPENROUTER_API_KEY and OpenAI:
            self.client = OpenAI(api_key=settings.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
            self.enabled = True

    def score_and_blurb(self, job: Job) -> Job:
        if not self.enabled:
            return job
        prompt = f"""
You are evaluating a job for a senior data/analytics leader with this background:
- 17+ years leading data science, analytics, marketing analytics (CDP, identity graph), cloud platforms, BI.
- Seeks roles like CDO, VP/Director of Data/Analytics, Head of Data, Data Strategy/Transformation.
Job (JSON):
{job.model_dump_json()}
Return JSON with:
- score: 0-100 strategic fit
- blurb: a single sentence for a "Why I'm a fit" field (<=220 chars, no names)
"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )
            txt = (resp.choices[0].message.content or "").strip()
            data = json.loads(txt)
            job.llm_score = float(data.get("score", 0))
            job.llm_blurb = str(data.get("blurb", ""))[:220]
        except Exception:
            # Soft-fail: keep job as-is
            pass
        return job

ASSESSMENT_TERMS = [t.strip().lower() for t in settings.ASSESSMENT_TERMS if t.strip()]

def detect_assessment(text: str) -> Tuple[int, str]:
    if not text:
        return (0, "")
    low = text.lower()
    hits = [term for term in ASSESSMENT_TERMS if term and term in low]
    return (1 if hits else 0, ", ".join(dict.fromkeys(hits)))
