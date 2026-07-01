import re
from datetime import datetime


REVIEW_STATUS_OPTIONS = ("visible", "pending", "hidden", "deleted", "reported")
REPORT_STATUS_OPTIONS = ("pending", "resolved", "rejected")
REVIEW_REPORT_REASONS = (
    "허위 리뷰",
    "욕설/비방",
    "개인정보 노출",
    "사생활 침해",
    "명예훼손 우려",
    "광고/스팸",
    "기타",
)

REVIEW_POLICY_NOTICE = (
    "실제 이용 경험을 바탕으로 작성해 주세요. 허위사실, 욕설, 인신공격, 개인정보 공개, "
    "사생활 침해, 차별·혐오 표현이 포함된 리뷰는 숨김 또는 삭제될 수 있으며 작성자에게 "
    "법적 책임이 발생할 수 있습니다."
)

LEGAL_RESPONSIBILITY_NOTICE = (
    "본인은 실제 이용 경험에 근거하여 리뷰를 작성하며, 허위사실 또는 타인의 권리를 "
    "침해하는 내용을 작성하지 않았음을 확인합니다."
)

RISK_WARNING_MESSAGE = (
    "리뷰에 개인정보, 욕설, 인신공격 또는 법적 분쟁 가능성이 있는 표현이 포함되어 있습니다. "
    "실제 경험 중심의 표현으로 수정해 주세요."
)

SAFER_REVIEW_EXAMPLES = [
    {
        "risk": "OOO 디자이너 인성 최악이에요.",
        "safe": "상담 과정에서 응대가 다소 불친절하게 느껴졌습니다.",
    },
    {
        "risk": "여기 사기치는 곳이에요.",
        "safe": "예약 전 안내받은 내용과 실제 결제 금액에 차이가 있어 아쉬웠습니다.",
    },
    {
        "risk": "실력 없는 사람입니다.",
        "safe": "제가 기대했던 스타일과 결과물이 달라 아쉬웠습니다.",
    },
]

REVIEW_STORE = []
REPORT_STORE = []

_PROFANITY_PATTERNS = [
    "씨발",
    "시발",
    "ㅅㅂ",
    "병신",
    "미친",
    "개새",
    "꺼져",
    "좆",
    "ㅈ같",
]
_PERSONAL_ATTACK_PATTERNS = [
    "쓰레기",
    "망해라",
    "인성 최악",
    "양심 없다",
    "양심없",
    "실력 없는",
    "실력없",
    "최악이에요",
    "인간도 아니다",
]
_DEFAMATION_RISK_PATTERNS = [
    "사기꾼",
    "사기치는",
    "사기 당",
    "먹튀",
    "불법",
    "범죄",
    "허위",
]
_HATE_SPEECH_PATTERNS = [
    "혐오",
    "장애인 비하",
    "외국인 꺼져",
    "여자라서",
    "남자라서",
]
_SPAM_PATTERNS = [
    "무료 이벤트",
    "수익 보장",
    "카톡 문의",
    "카카오 문의",
    "오픈채팅",
    "링크 클릭",
]

_PHONE_RE = re.compile(r"(?<!\d)(01[016789])[-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_EXTERNAL_ID_RE = re.compile(r"(?<![\w.])@([A-Za-z0-9_][A-Za-z0-9._]{1,29})(?!\.[A-Za-z]{2,})(?![\w.])")
_KAKAO_RE = re.compile(r"(카카오톡|카톡|kakao|오픈채팅)\s*(id|아이디|ID)?\s*[:：]?\s*([A-Za-z0-9._-]{3,30})", re.IGNORECASE)
_BIRTH_RE = re.compile(r"(?<!\d)(?:\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[-\s]?[1-4]\d{6}|\d{4}[.-]\d{1,2}[.-]\d{1,2})(?!\d)")
_ADDRESS_RE = re.compile(r"([가-힣A-Za-z0-9]+(?:시|군|구)\s+[가-힣A-Za-z0-9]+(?:로|길)\s*\d{1,4}(?:-\d{1,4})?)")
_REAL_NAME_ATTACK_RE = re.compile(r"[가-힣]{2,4}\s*(디자이너|쌤|원장|실장|선생님)?\s*(인성 최악|사기꾼|쓰레기|망해라|양심 없다|실력 없)")


def _contains_any(text, patterns):
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def detectReviewRisks(text):
    """Detect legal, privacy, and community-safety risk types in review text."""
    text = text or ""
    detected = []
    if _contains_any(text, _PROFANITY_PATTERNS):
        detected.append("profanity")
    if _contains_any(text, _PERSONAL_ATTACK_PATTERNS):
        detected.append("personal_attack")
    if _contains_any(text, _DEFAMATION_RISK_PATTERNS):
        detected.append("defamation_risk")
    if _PHONE_RE.search(text) or _EMAIL_RE.search(text) or _BIRTH_RE.search(text) or _ADDRESS_RE.search(text):
        detected.append("personal_info")
    if _EXTERNAL_ID_RE.search(text) or _KAKAO_RE.search(text):
        detected.append("external_contact")
    if _REAL_NAME_ATTACK_RE.search(text):
        detected.append("real_name_attack")
    if _contains_any(text, _SPAM_PATTERNS):
        detected.append("spam")
    if _contains_any(text, _HATE_SPEECH_PATTERNS):
        detected.append("hate_speech")
    if _BIRTH_RE.search(text) or "집주소" in text or "사생활" in text:
        detected.append("privacy_violation")
    return list(dict.fromkeys(detected))


def maskPersonalInfo(text):
    """Mask phone numbers, email addresses, external IDs, Kakao IDs, and address-like strings."""
    text = text or ""

    def mask_phone(match):
        return f"{match.group(1)}-****-****"

    def mask_email(match):
        return f"{match.group(1)}****{match.group(2)}"

    masked = _EXTERNAL_ID_RE.sub("@****", text)
    masked = _KAKAO_RE.sub(lambda match: f"{match.group(1)} ID ****", masked)
    masked = _PHONE_RE.sub(mask_phone, masked)
    masked = _EMAIL_RE.sub(mask_email, masked)
    masked = _BIRTH_RE.sub("생년월일/주민번호 ****", masked)
    masked = _ADDRESS_RE.sub("상세주소 ****", masked)
    return masked


def calculateRiskScore(detectedRiskTypes):
    weights = {
        "profanity": 35,
        "personal_attack": 35,
        "defamation_risk": 45,
        "personal_info": 45,
        "external_contact": 35,
        "real_name_attack": 50,
        "spam": 25,
        "hate_speech": 50,
        "privacy_violation": 50,
    }
    return min(100, sum(weights.get(risk_type, 10) for risk_type in set(detectedRiskTypes or [])))


def _combined_review_text(review):
    fields = [
        "visitPurpose",
        "positiveComment",
        "negativeComment",
        "reviewText",
        "shopName",
        "artistName",
        "displayName",
        "nickname",
    ]
    return "\n".join(str(review.get(field, "") or "") for field in fields)


def validateReviewBeforeSubmit(review):
    review = review or {}
    detected = detectReviewRisks(_combined_review_text(review))
    risk_score = calculateRiskScore(detected)
    missing = []
    if not review.get("reviewPolicyAgreed"):
        missing.append("reviewPolicyAgreed")
    if not review.get("legalResponsibilityConfirmed"):
        missing.append("legalResponsibilityConfirmed")
    if not review.get("rating"):
        missing.append("rating")
    if not (review.get("reviewText") or "").strip():
        missing.append("reviewText")

    blocking_risks = {
        "profanity",
        "personal_attack",
        "defamation_risk",
        "real_name_attack",
        "hate_speech",
        "privacy_violation",
    }
    personal_risks = {"personal_info", "external_contact"}
    should_block = bool(blocking_risks.intersection(detected)) or bool(missing)
    should_mask = bool(personal_risks.intersection(detected))
    suggested_status = "pending" if detected else "visible"
    if risk_score >= 70:
        should_block = True
        suggested_status = "pending"

    return {
        "canSubmit": not should_block,
        "shouldBlock": should_block,
        "shouldMask": should_mask,
        "status": suggested_status,
        "riskScore": risk_score,
        "detectedRiskTypes": detected,
        "missingFields": missing,
        "message": RISK_WARNING_MESSAGE if detected else "",
        "safeExamples": SAFER_REVIEW_EXAMPLES,
    }


def _masked_review_copy(review):
    copied = dict(review or {})
    for field in ("positiveComment", "negativeComment", "reviewText", "visitPurpose", "artistName", "artist_name"):
        copied[field] = maskPersonalInfo(copied.get(field, ""))
    return copied


def submitReview(review):
    validation = validateReviewBeforeSubmit(review)
    if not validation["canSubmit"]:
        raise ValueError(validation["message"] or "리뷰 제출 조건을 확인해주세요.")
    saved = _masked_review_copy(review)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    saved.setdefault("id", f"review_{len(REVIEW_STORE) + 1}_{int(datetime.now().timestamp())}")
    saved.setdefault("status", validation["status"])
    saved["riskScore"] = validation["riskScore"]
    saved["detectedRiskTypes"] = validation["detectedRiskTypes"]
    saved.setdefault("createdAt", now)
    saved["updatedAt"] = now
    REVIEW_STORE.append(saved)
    return saved


def reportReview(reviewId, reason, detail):
    report = {
        "id": f"report_{len(REPORT_STORE) + 1}_{int(datetime.now().timestamp())}",
        "reportId": f"report_{len(REPORT_STORE) + 1}_{int(datetime.now().timestamp())}",
        "reviewId": reviewId,
        "reporterUserId": "local_user",
        "reason": reason,
        "detail": detail or "",
        "status": "pending",
        "adminMemo": "",
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resolvedAt": None,
    }
    REPORT_STORE.append(report)
    reports_for_review = [item for item in REPORT_STORE if item.get("reviewId") == reviewId]
    if len(reports_for_review) >= 3:
        updateReviewStatus(reviewId, "hidden", "신고 3회 이상 자동 숨김")
    return report


def updateReviewStatus(reviewId, status, adminMemo):
    if status not in REVIEW_STATUS_OPTIONS:
        raise ValueError("지원하지 않는 리뷰 상태입니다.")
    for review in REVIEW_STORE:
        if review.get("id") == reviewId:
            review["status"] = status
            review["adminMemo"] = adminMemo or review.get("adminMemo", "")
            review["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            return review
    return None
