COMMUNITY_POST_TYPE_ORDER = {
    "리뷰": 0,
    "질문": 1,
    "자유": 2,
    "자유게시판": 2,
    "공유": 2,
    "스냅": 3,
    "비디오": 4,
}


def default_community_posts():
    return [
        {
            "type": "community",
            "post_type": "질문",
            "category": "헤어",
            "title": "앞머리 자를까 말까 봐주세요",
            "subtitle": "익명뷰티러 · 강남 · 12분 전",
            "meta": "댓글 8 · 저장 14 · 조회 120",
            "description": "중단발이고 얼굴형이 긴 편이에요. 시스루뱅이 나을지 풀뱅이 나을지 고민돼요.",
            "badge": "질문",
            "tags": ["앞머리", "중단발", "상담"],
        },
        {
            "type": "community",
            "post_type": "리뷰",
            "category": "네일아트",
            "title": "화이트 프렌치 네일 2주차 후기",
            "subtitle": "네일기록 · 홍대 · 36분 전",
            "meta": "만족도 4.5 · 댓글 3 · 저장 21",
            "description": "손톱이 짧은 편인데 라인을 얇게 잡아줘서 손이 길어 보여요. 유지력도 괜찮아서 다음에도 참고하고 싶어요.",
            "badge": "리뷰",
            "rating": 4.5,
            "verifiedVisit": True,
            "tags": ["프렌치", "유지력", "짧은손톱"],
        },
        {
            "type": "community",
            "post_type": "자유",
            "category": "메이크업",
            "title": "봄라이트 데일리 메이크업 조합",
            "subtitle": "피치무드 · 성수 · 1시간 전",
            "meta": "좋아요 77 · 저장 44 · 댓글 6",
            "description": "피치 베이스에 로지 블러셔를 얹으니 얼굴이 훨씬 맑아 보여요. 면접 메이크업으로도 괜찮았어요.",
            "badge": "자유",
            "tags": ["봄라이트", "데일리", "면접"],
        },
        {
            "type": "community",
            "post_type": "질문",
            "category": "반영구",
            "title": "자연눈썹 가격 25만원이면 적당한가요?",
            "subtitle": "첫방문 · 잠실 · 2시간 전",
            "meta": "댓글 11 · 저장 18 · 조회 488",
            "description": "첫 반영구라 너무 진해질까 걱정돼요. 리터치 포함 가격인지도 꼭 확인해야 할까요?",
            "badge": "질문",
            "tags": ["반영구", "가격", "리터치"],
        },
        {
            "type": "community",
            "post_type": "자유",
            "category": "웨딩",
            "title": "하객 메이크업 셀프로 할지 도움 받을지 고민",
            "subtitle": "하객룩고민 · 마포 · 3시간 전",
            "meta": "댓글 5 · 저장 12 · 조회 271",
            "description": "사진 많이 찍히는 자리라 전문가 도움을 받을까 하는데, 하객 메이크업은 어느 정도가 과하지 않을까요?",
            "badge": "자유",
            "tags": ["하객", "메이크업", "웨딩"],
        },
        {
            "type": "community",
            "post_type": "스냅",
            "category": "포토",
            "title": "프로필 촬영 전날 체크리스트",
            "subtitle": "프로필준비 · 합정 · 5시간 전",
            "meta": "좋아요 54 · 저장 37 · 댓글 2",
            "description": "의상 2벌, 립 컬러 2개, 헤어 고정 스프레이, 보조배터리는 꼭 챙기면 좋아요.",
            "badge": "스냅",
            "tags": ["프로필", "촬영", "준비물"],
        },
        {
            "type": "community",
            "post_type": "비디오",
            "category": "반영구",
            "title": "눈썹 관리 전 체크리스트 영상",
            "subtitle": "브로우메모 · 건대 · 6시간 전",
            "meta": "좋아요 42 · 저장 31 · 댓글 9",
            "description": "관리 전 피부 상태, 리터치 일정, 당일 세안 주의점을 짧게 정리했어요.",
            "badge": "비디오",
            "tags": ["반영구", "체크리스트", "영상"],
        },
    ]


def extract_metric(text, label):
    try:
        after = str(text).split(label, 1)[1].strip()
        value = after.split(" ", 1)[0].replace("개", "")
        return int(value)
    except (IndexError, TypeError, ValueError):
        return 0


def video_duration_seconds(duration):
    parts = str(duration or "0:00").strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(float(parts[0]))
    except (TypeError, ValueError):
        return 0


def is_short_video(video):
    seconds = video_duration_seconds(video.get("duration", "0:59"))
    return 0 <= seconds <= 60


def default_video_items():
    return [
        {"id": "video_hair_1", "title": "앞머리 들뜸 30초 정리법", "subtitle": "드라이기와 작은 롤빗으로 아침에 빠르게", "badge": "TIP", "category": "헤어", "duration": "0:48", "views": "3.2만"},
        {"id": "video_hair_2", "title": "고데기 없이 볼륨 살리는 법", "subtitle": "뿌리 볼륨이 금방 죽는 사람들을 위한 팁", "badge": "TIP", "category": "헤어", "duration": "0:57", "views": "2.8만"},
        {"id": "video_makeup_1", "title": "베이스 안 뜨게 바르는 순서", "subtitle": "기초 단계 후 5분 기다리는 작은 습관", "badge": "TIP", "category": "메이크업", "duration": "0:52", "views": "4.1만"},
        {"id": "video_makeup_2", "title": "립 하나로 생기 살리는 조합", "subtitle": "볼과 입술에 같이 쓰는 데일리 컬러", "badge": "TIP", "category": "메이크업", "duration": "0:44", "views": "5.6만"},
        {"id": "video_nail_1", "title": "네일 오래 가는 손끝 관리", "subtitle": "큐티클 오일 바르는 타이밍 공유", "badge": "TIP", "category": "네일아트", "duration": "0:45", "views": "2.1만"},
        {"id": "video_nail_2", "title": "짧은 손톱 컬러 고르는 법", "subtitle": "손이 길어 보이는 누드톤 기준", "badge": "TIP", "category": "네일아트", "duration": "0:55", "views": "1.9만"},
        {"id": "video_semi_1", "title": "자연눈썹 탈각 기간 관리", "subtitle": "첫 주에 피해야 할 습관과 보습 타이밍", "badge": "TIP", "category": "반영구", "duration": "0:51", "views": "2.6만"},
        {"id": "video_semi_2", "title": "입술 반영구 전 체크", "subtitle": "컬러 상담 전에 확인하면 좋은 포인트", "badge": "TIP", "category": "반영구", "duration": "0:47", "views": "1.7만"},
        {"id": "video_wedding_1", "title": "하객 메이크업 과하지 않게", "subtitle": "사진에서 깔끔하게 보이는 포인트", "badge": "TIP", "category": "웨딩", "duration": "0:58", "views": "6.3만"},
        {"id": "video_wedding_2", "title": "셀프 웨이브 고정 루틴", "subtitle": "오래 앉아 있어도 덜 풀리는 방법", "badge": "TIP", "category": "웨딩", "duration": "0:54", "views": "3.7만"},
        {"id": "video_photo_1", "title": "프로필 촬영 전날 체크", "subtitle": "붓기와 의상 준비를 한 번에 점검", "badge": "TIP", "category": "포토", "duration": "0:56", "views": "2.5만"},
        {"id": "video_photo_2", "title": "폰으로 찍는 감성 포토 팁", "subtitle": "창가 자연광과 구도 잡는 법", "badge": "TIP", "category": "포토", "duration": "0:49", "views": "4.4만"},
    ]
