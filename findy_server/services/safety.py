import re
from typing import Dict, List


PROFANITY = {"씨발", "병신", "미친", "꺼져", "좆", "개새"}
PERSONAL_ATTACKS = {"사기꾼", "쓰레기", "망해라", "인성 최악", "양심 없다", "실력 없는"}
HATE_WORDS = {"혐오", "장애인 비하", "외국인 혐오"}


RISK_SCORES = {
    "profanity": 35,
    "personal_attack": 35,
    "defamation_risk": 30,
    "personal_info": 40,
    "phone_number": 45,
    "email": 35,
    "address": 35,
    "external_contact": 30,
    "real_name_attack": 45,
    "spam": 25,
    "hate_speech": 45,
    "privacy_violation": 45,
    "copyright_risk": 30,
}


def detect_content_risks(text: str) -> List[str]:
    content = text or ""
    risks = set()
    if any(word in content for word in PROFANITY):
        risks.add("profanity")
    if any(word in content for word in PERSONAL_ATTACKS):
        risks.add("personal_attack")
        risks.add("defamation_risk")
    if any(word in content for word in HATE_WORDS):
        risks.add("hate_speech")
    if re.search(r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}", content):
        risks.add("phone_number")
        risks.add("personal_info")
    if re.search(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}", content):
        risks.add("email")
        risks.add("personal_info")
    if re.search(r"@[A-Za-z0-9._]{3,}", content) or "카톡" in content or "카카오톡" in content:
        risks.add("external_contact")
    if re.search(r"[가-힣]{2,4}\s*(디자이너|원장|쌤)?\s*(사기꾼|쓰레기|인성 최악|실력 없는)", content):
        risks.add("real_name_attack")
    if re.search(r"(서울|부산|대구|인천|광주|대전|울산|경기).{0,20}(동|로|길)\s?\d+", content):
        risks.add("address")
        risks.add("personal_info")
    if len(re.findall(r"https?://|www\.", content)) >= 2:
        risks.add("spam")
    return sorted(risks)


def mask_personal_info(text: str) -> str:
    masked = text or ""
    masked = re.sub(r"(01[016789])[-\s]?(\d{3,4})[-\s]?(\d{4})", r"\1-****-****", masked)
    masked = re.sub(r"([\w.\-+])[\w.\-+]*(@[\w.\-]+\.[A-Za-z]{2,})", r"\1****\2", masked)
    masked = re.sub(r"@[A-Za-z0-9._]{3,}", "@****", masked)
    return masked


def calculate_risk_score(risk_types: List[str]) -> int:
    return min(100, sum(RISK_SCORES.get(risk_type, 10) for risk_type in set(risk_types)))


def validate_content(text: str) -> Dict[str, object]:
    risk_types = detect_content_risks(text)
    risk_score = calculate_risk_score(risk_types)
    if risk_score >= 75:
        status = "blocked"
    elif risk_score >= 35:
        status = "pending"
    else:
        status = "visible"
    return {
        "riskTypes": risk_types,
        "riskScore": risk_score,
        "maskedText": mask_personal_info(text),
        "status": status,
        "canSubmit": status != "blocked",
    }

