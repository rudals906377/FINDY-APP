import re
from datetime import datetime


CONTENT_STATUS_OPTIONS = ("visible", "pending", "hidden", "deleted", "reported")
REPORT_STATUS_OPTIONS = ("pending", "resolved", "rejected")
REPORT_REASONS = (
    "허위 정보",
    "욕설/비방",
    "개인정보 노출",
    "명예훼손 우려",
    "사생활 침해",
    "저작권/초상권 침해",
    "광고/스팸",
    "음란물 또는 불법 콘텐츠",
    "기타",
)
IMAGE_REPORT_REASONS = (
    "초상권 침해",
    "개인정보 노출",
    "저작권 침해",
    "음란물",
    "불법촬영물",
    "혐오·폭력 콘텐츠",
    "광고·스팸",
    "기타",
)

CONTENT_POLICY_NOTICE = (
    "실제 경험과 의견을 바탕으로 작성해 주세요. 허위사실, 욕설, 인신공격, "
    "개인정보·사생활 공개, 타인의 사진·콘텐츠 무단 게시물은 숨김 또는 삭제될 수 "
    "있으며 법적 책임이 발생할 수 있습니다."
)

PHOTO_RIGHTS_NOTICE = (
    "본인은 업로드하는 사진에 대하여 필요한 저작권, 초상권 및 사용 권한을 보유하고 "
    "있음을 확인합니다. 타인의 얼굴, 개인정보 또는 저작물을 권한 없이 게시할 경우 "
    "게시물이 삭제되거나 이용이 제한될 수 있습니다."
)

RISK_WARNING_MESSAGE = (
    "개인정보, 욕설, 인신공격 또는 법적 분쟁 가능성이 있는 표현이 포함되어 있습니다. "
    "실제 경험 중심의 표현으로 수정해 주세요."
)

SAFE_EXPRESSION_SUGGESTIONS = [
    {
        "risk": "OOO는 사기꾼이에요.",
        "safe": "안내받은 내용과 실제 진행 과정에 차이가 있어 아쉬웠습니다.",
    },
    {
        "risk": "인성 최악이에요.",
        "safe": "상담 또는 응대 과정에서 불편함을 느꼈습니다.",
    },
    {
        "risk": "실력 없는 디자이너예요.",
        "safe": "제가 기대했던 스타일과 결과가 달라 아쉬웠습니다.",
    },
]

_PROFANITY_PATTERNS = ("씨발", "시발", "ㅅㅂ", "병신", "미친", "개새", "꺼져", "좆", "ㅈ같")
_PERSONAL_ATTACK_PATTERNS = (
    "쓰레기",
    "망해라",
    "인성 최악",
    "양심 없다",
    "양심없",
    "실력 없는",
    "실력없",
    "인간도 아니다",
)
_DEFAMATION_PATTERNS = ("사기꾼", "사기치는", "먹튀", "범죄자", "불법업소", "허위시술")
_HATE_PATTERNS = ("혐오", "장애인 비하", "외국인 꺼져", "여자라서", "남자라서")
_SPAM_PATTERNS = ("무료 이벤트", "수익 보장", "카톡 문의", "오픈채팅", "링크 클릭", "협찬문의")
_COPYRIGHT_PATTERNS = ("무단 캡처", "불펌", "퍼왔어요", "출처 모름", "도용")

_PHONE_RE = re.compile(r"(?<!\d)(01[016789])[-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_EXTERNAL_ID_RE = re.compile(r"(?<![\w.])@([A-Za-z0-9_][A-Za-z0-9._]{1,29})(?!\.[A-Za-z]{2,})(?![\w.])")
_KAKAO_RE = re.compile(r"(카카오톡|카톡|kakao|오픈채팅)\s*(id|아이디|ID)?\s*[:：]?\s*([A-Za-z0-9._-]{3,30})", re.IGNORECASE)
_BIRTH_RE = re.compile(r"(?<!\d)(?:\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[-\s]?[1-4]\d{6}|\d{4}[.-]\d{1,2}[.-]\d{1,2})(?!\d)")
_ADDRESS_RE = re.compile(r"([가-힣A-Za-z0-9]+(?:시|군|구)\s+[가-힣A-Za-z0-9]+(?:로|길)\s*\d{1,4}(?:-\d{1,4})?)")
_REAL_NAME_ATTACK_RE = re.compile(r"[가-힣]{2,4}\s*(디자이너|쌤|원장|실장|선생님)?\s*(인성 최악|사기꾼|쓰레기|망해라|양심 없다|실력 없)")


def _contains_any(text, patterns):
    lowered = (text or "").lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def detectPotentialRealNameAttack(text):
    return bool(_REAL_NAME_ATTACK_RE.search(text or ""))


def detectContentRisks(text):
    text = text or ""
    risks = []
    if _contains_any(text, _PROFANITY_PATTERNS):
        risks.append("profanity")
    if _contains_any(text, _PERSONAL_ATTACK_PATTERNS):
        risks.append("personal_attack")
    if _contains_any(text, _DEFAMATION_PATTERNS):
        risks.append("defamation_risk")
    if _PHONE_RE.search(text):
        risks.extend(["personal_info", "phone_number"])
    if _EMAIL_RE.search(text):
        risks.extend(["personal_info", "email"])
    if _ADDRESS_RE.search(text):
        risks.extend(["personal_info", "address"])
    if _EXTERNAL_ID_RE.search(text) or _KAKAO_RE.search(text):
        risks.extend(["personal_info", "external_contact"])
    if _BIRTH_RE.search(text) or "집주소" in text or "사생활" in text:
        risks.extend(["personal_info", "privacy_violation"])
    if detectPotentialRealNameAttack(text):
        risks.append("real_name_attack")
    if _contains_any(text, _SPAM_PATTERNS):
        risks.append("spam")
    if _contains_any(text, _HATE_PATTERNS):
        risks.append("hate_speech")
    if _contains_any(text, _COPYRIGHT_PATTERNS):
        risks.append("copyright_risk")
    return list(dict.fromkeys(risks))


def maskPersonalInfo(text):
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


def calculateRiskScore(riskTypes):
    weights = {
        "profanity": 35,
        "personal_attack": 35,
        "defamation_risk": 45,
        "personal_info": 45,
        "phone_number": 30,
        "email": 30,
        "address": 35,
        "external_contact": 35,
        "real_name_attack": 50,
        "spam": 25,
        "hate_speech": 55,
        "privacy_violation": 55,
        "copyright_risk": 30,
    }
    return min(100, sum(weights.get(risk_type, 10) for risk_type in set(riskTypes or [])))


def _content_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, dict):
        return ""
    fields = ("title", "description", "content", "reviewText", "comment", "artistName", "shopName")
    return "\n".join(str(content.get(field, "") or "") for field in fields)


def validateContentBeforeSubmit(content):
    text = _content_text(content)
    risks = detectContentRisks(text)
    score = calculateRiskScore(risks)
    high_risks = {"hate_speech", "privacy_violation", "real_name_attack"}
    blocking_risks = {"profanity", "personal_attack"}
    has_high = bool(high_risks.intersection(risks)) or score >= 75
    has_blocking = bool(blocking_risks.intersection(risks))
    has_personal = bool({"personal_info", "phone_number", "email", "address", "external_contact"}.intersection(risks))
    status = "visible"
    if risks:
        status = "pending" if score >= 35 else "visible"
    return {
        "canSubmit": not (has_high or has_blocking),
        "shouldBlock": has_high or has_blocking,
        "shouldMask": has_personal,
        "status": status,
        "riskScore": score,
        "detectedRiskTypes": risks,
        "maskedText": maskPersonalInfo(text) if has_personal else text,
        "message": RISK_WARNING_MESSAGE if risks else "",
        "safeExamples": SAFE_EXPRESSION_SUGGESTIONS,
    }


COMMUNITY_POST_STORE = []
CONTENT_REPORT_STORE = []
ADMIN_ACTION_LOG = []


def submitCommunityPost(post):
    validation = validateContentBeforeSubmit(post)
    if not validation["canSubmit"]:
        raise ValueError(validation["message"] or "게시글 제출 조건을 확인해주세요.")
    saved = dict(post or {})
    saved.setdefault("id", f"post_{len(COMMUNITY_POST_STORE) + 1}_{int(datetime.now().timestamp())}")
    saved.setdefault("status", validation["status"])
    saved["riskScore"] = validation["riskScore"]
    saved["detectedRiskTypes"] = validation["detectedRiskTypes"]
    saved.setdefault("createdAt", datetime.now().strftime("%Y-%m-%d %H:%M"))
    saved["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    COMMUNITY_POST_STORE.append(saved)
    return saved


def reportContent(contentId, reason, detail, targetType="post", reporterUserId="local_user"):
    report = {
        "id": f"content_report_{len(CONTENT_REPORT_STORE) + 1}_{int(datetime.now().timestamp())}",
        "reporterUserId": reporterUserId,
        "targetType": targetType,
        "targetId": contentId,
        "reason": reason,
        "detail": detail or "",
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "pending",
        "adminMemo": "",
        "resolvedAt": "",
    }
    CONTENT_REPORT_STORE.append(report)
    return report


def updateContentStatus(contentId, status, adminMemo="", adminUserId="local_admin", targetType="post"):
    if status not in CONTENT_STATUS_OPTIONS:
        raise ValueError("지원하지 않는 콘텐츠 상태입니다.")
    action = {
        "id": f"admin_action_{len(ADMIN_ACTION_LOG) + 1}_{int(datetime.now().timestamp())}",
        "adminUserId": adminUserId,
        "actionType": f"status:{status}",
        "targetType": targetType,
        "targetId": contentId,
        "reason": adminMemo or "",
        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    ADMIN_ACTION_LOG.append(action)
    return action
