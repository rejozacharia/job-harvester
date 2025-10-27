from pydantic_settings import BaseSettings
<<<<<<< HEAD
from pydantic import Field, field_validator
=======
from pydantic import Field
>>>>>>> main
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
<<<<<<< HEAD
    SCHEDULE_CRONS: List[str] = Field(default_factory=lambda: ["40 7 * * *"])
    JOB_STATUS_CHOICES: List[str] = Field(default_factory=lambda: [
        "harvested","researching","applied","interviewing","offer","rejected","archived"
    ])
=======
>>>>>>> main

    class Config:
        env_file = ".env"

<<<<<<< HEAD
    @staticmethod
    def _split_env_list(value: str) -> List[str]:
        import re
        return [item.strip() for item in re.split(r"[;,\n]+", value) if item.strip()]

    @field_validator(
        "QUERY_TITLES",
        "QUERY_KEYWORDS",
        "LOCATIONS",
        "ASSESSMENT_TERMS",
        "SCHEDULE_CRONS",
        "JOB_STATUS_CHOICES",
        mode="before",
    )
    def _coerce_list(cls, value):
        if isinstance(value, str):
            return cls._split_env_list(value)
        return value

    @field_validator("JOB_STATUS_CHOICES", mode="after")
    def _normalize_statuses(cls, value: List[str]) -> List[str]:
        return [item.lower() for item in value]

=======
>>>>>>> main
settings = Settings()
