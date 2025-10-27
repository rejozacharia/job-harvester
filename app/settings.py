from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    SERPAPI_KEY: str = ""
    QUERY_TITLES: List[str] = Field(default_factory=lambda: [
        "Chief Data Officer","VP Data Science","VP Analytics",
        "Head of Data","Director Analytics","Director Marketing Analytics"
    ])
    QUERY_KEYWORDS: List[str] = []
    LOCATIONS: List[str] = ["Remote","Chicago, IL, USA","Illinois"]
    REMOTE_ONLY: bool = False
    MAX_RESULTS: int = 50

    ENABLE_ASSESSMENT_FILTER: bool = False
    ENABLE_ASSESSMENT_BOOST: bool = True
    ASSESSMENT_TERMS: List[str] = [
        "assessment","aptitude","cognitive","reasoning test","case study",
        "business case","analytical exercise","situational judgment","evaluation","challenge"
    ]
    ASSESSMENT_SCORE_BOOST: float = 15.0

    ENABLE_FOLLOW_LINK: bool = True
    HTTP_TIMEOUT_SECS: int = 18
    MAX_HTML_CHARS: int = 120000

    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    OUTPUT_DIR: str = "/app/output"
    DB_PATH: str = "/app/data/jobs.db"

    TZ: str = "America/Chicago"

    class Config:
        env_file = ".env"

settings = Settings()
