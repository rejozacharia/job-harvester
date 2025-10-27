from bs4 import BeautifulSoup
import requests
from .settings import settings

NOISE_TAGS = ["script","style","noscript","header","footer","nav","svg"]


def fetch_full_description(url: str) -> str:
    if not (settings.ENABLE_FOLLOW_LINK and url):
        return ""
    try:
        resp = requests.get(url, timeout=settings.HTTP_TIMEOUT_SECS, headers={"User-Agent":"Mozilla/5.0"})
        html = resp.text[:settings.MAX_HTML_CHARS]
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(NOISE_TAGS):
            tag.decompose()
        text = " ".join(soup.get_text(" ").split())
        return text[:20000]
    except Exception:
        return ""
