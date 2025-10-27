import hashlib
import re
import requests
from typing import List
from dateutil import parser as dtparse
from .models import Job
from .settings import settings

SERP_BASE = "https://serpapi.com/search.json"
RELATIVE_DATE_PAT = re.compile(r"(\\d+)\\s*(day|hour|minute|week|month|year)s? ago", re.I)


def _hash_id(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:32]


def _normalize_date(s: str | None) -> str:
    if not s:
        return ""
    try:
        return dtparse.parse(str(s)).isoformat()
    except Exception:
        pass
    m = RELATIVE_DATE_PAT.search(str(s))
    if not m:
        return ""
    from datetime import datetime, timedelta
    n = int(m.group(1)); unit = m.group(2).lower()
    now = datetime.utcnow()
    delta = {
        "minute": timedelta(minutes=n),
        "hour": timedelta(hours=n),
        "day": timedelta(days=n),
        "week": timedelta(weeks=n),
        "month": timedelta(days=30*n),
        "year": timedelta(days=365*n),
    }.get(unit, timedelta(0))
    return (now - delta).isoformat()


class SerpGoogleJobs:
    @staticmethod
    def search(query: str, location: str, remote_only: bool, max_results: int) -> List[Job]:
        if not settings.SERPAPI_KEY:
            return []
        params = {
            "engine": "google_jobs",
            "q": f"{query} remote" if remote_only else query,
            "hl": "en",
            "api_key": settings.SERPAPI_KEY,
            "chips": "date_posted:week",
            "location": location,
        }
        r = requests.get(SERP_BASE, params=params, timeout=settings.HTTP_TIMEOUT_SECS)
        if r.status_code != 200:
            return []
        data = r.json()
        results = []
        for it in data.get("jobs_results", [])[:max_results]:
            title = (it.get("title") or "").strip()
            company = (it.get("company_name") or "").strip()
            loc = (it.get("location") or "").strip()
            via = (it.get("via") or "").strip()
            url = it.get("link") or (it.get("related_links", [{}])[0].get("link")) or ""
            if not url:
                apps = it.get("apply_options", [])
                url = (apps and apps[0].get("link")) or ""
            desc = (it.get("description") or "")[:2000]
            posted_iso = _normalize_date((it.get("detected_extensions", {}) or {}).get("posted_at"))
            salary = (it.get("detected_extensions", {}) or {}).get("salary", "")
            uid = _hash_id(url or f"{title}-{company}-{loc}")
            results.append(Job(id=uid, title=title, company=company, location=loc, via=via,
                               posted_at=posted_iso, url=url, source="google_jobs",
                               description=desc, salary=salary))
        return results


class SerpLinkedInJobs:
    @staticmethod
    def search(query: str, location: str, remote_only: bool, max_results: int) -> List[Job]:
        if not settings.SERPAPI_KEY:
            return []
        params = {
            "engine": "linkedin_jobs",
            "keywords": query,
            "location": location,
            "api_key": settings.SERPAPI_KEY,
            "remote": "true" if remote_only else None,
        }
        # Clean None values
        params = {k: v for k, v in params.items() if v is not None}
        r = requests.get(SERP_BASE, params=params, timeout=settings.HTTP_TIMEOUT_SECS)
        if r.status_code != 200:
            return []
        data = r.json()
        results = []
        for it in data.get("jobs", [])[:max_results]:
            title = (it.get("title") or "").strip()
            company = ((it.get("company") or {}).get("name") or "").strip()
            loc = (it.get("location") or "").strip()
            url = it.get("link") or ""
            posted_iso = _normalize_date(it.get("listed_at", ""))
            uid = _hash_id(url or f"{title}-{company}-{loc}")
            results.append(Job(id=uid, title=title, company=company, location=loc, via="LinkedIn",
                               posted_at=posted_iso, url=url, source="linkedin"))
        return results
