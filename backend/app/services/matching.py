from dataclasses import dataclass
from typing import List
import re

def _tokenize_skills(text: str) -> List[str]:
    parts = re.split(r"[^a-zA-Z0-9+#\.]+", text.lower())
    return [p for p in parts if p]

def _extract_skills(text: str) -> List[str]:
    keywords = [
        "python","java","javascript","typescript","react","node","fastapi","django","flask",
        "aws","gcp","azure","docker","kubernetes","sql","nosql","postgres","mysql","mongodb",
        "nlp","ml","ai","pytorch","tensorflow","sklearn","spacy","transformers",
        "c++","c#","go","rust","php","html","css","tailwind","next.js","nextjs","shadcn"
    ]
    set_kw = set(keywords)
    seen = set()
    result = []
    for tok in _tokenize_skills(text):
        if tok in set_kw and tok not in seen:
            seen.add(tok)
            result.append(tok)
    return result

def _normalize_must_have(skills_csv: str) -> List[str]:
    return [s.strip().lower() for s in skills_csv.split(',') if s.strip()]

@dataclass
class MatchItem:
    score: float
    missing_skills: List[str]
    remarks: str

async def score_resumes_against_jd(jd_text: str, resumes_text: List[str]) -> List[MatchItem]:
    jd_skills = set(_extract_skills(jd_text))
    items: List[MatchItem] = []
    for txt in resumes_text:
        res_skills = set(_extract_skills(txt))
        present = jd_skills.intersection(res_skills)
        missing = sorted(list(jd_skills - res_skills))
        total = max(len(jd_skills), 1)
        score = round(100.0 * len(present) / total, 2)
        remarks = "strong in " + ", ".join(sorted(list(present))[:3]) if present else "no key skills matched"
        items.append(MatchItem(score=score, missing_skills=missing, remarks=remarks))
    return items
