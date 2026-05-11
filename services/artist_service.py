from data.artists import BASE_ARTISTS
from data.categories import SUBCATEGORIES


DEFAULT_ARTIST_SCHEDULE = {
    "start": "09:00",
    "end": "22:00",
    "slot_minutes": 30,
    "breaks": [],
    "off_weekdays": [],
    "blocked_dates": [],
    "booking_days": 45,
    "services": None,
}

ARTIST_SCHEDULES = {
    "a1": {
        "start": "09:00",
        "end": "21:30",
        "breaks": [("13:00", "14:00")],
        "off_weekdays": [1],
        "services": ["커트", "컬러", "펌", "드라이", "모발 클리닉"],
    },
    "a2": {
        "start": "10:00",
        "end": "20:30",
        "breaks": [("12:30", "13:30")],
        "off_weekdays": [0],
        "services": ["데일리", "웨딩/하객", "면접/취업", "프로필/증명사진"],
    },
    "a3": {
        "start": "11:00",
        "end": "20:00",
        "breaks": [("15:00", "15:30")],
        "off_weekdays": [2],
        "services": ["젤네일", "케어", "아트/파츠", "이달의 네일"],
    },
    "a4": {
        "start": "10:00",
        "end": "21:00",
        "breaks": [("12:00", "13:00")],
        "off_weekdays": [0],
        "services": ["프로필/증명사진", "데일리 스냅", "화보 촬영", "컨셉 촬영"],
    },
    "a5": {
        "start": "09:30",
        "end": "19:30",
        "breaks": [("12:00", "13:00")],
        "off_weekdays": [1],
        "services": ["신부 메이크업", "신부 헤어", "혼주 스타일링", "하객 스타일링"],
    },
    "a6": {
        "start": "10:00",
        "end": "20:00",
        "breaks": [("13:30", "14:00")],
        "off_weekdays": [6],
        "services": ["눈썹", "아이라인", "입술", "리터치/보정"],
    },
    "a7": {
        "start": "09:30",
        "end": "21:30",
        "breaks": [("11:30", "12:30")],
        "off_weekdays": [3],
        "services": ["데일리 스냅", "커플 스냅", "웨딩 스냅", "프로필 스냅"],
    },
    "a8": {
        "start": "11:00",
        "end": "22:00",
        "breaks": [("14:00", "14:30")],
        "off_weekdays": [2],
        "services": ["커트", "컬러", "펌", "두피 케어"],
    },
}


def list_artists(category=None):
    if not category or category == "전체":
        return BASE_ARTISTS
    return [artist for artist in BASE_ARTISTS if artist.get("category") == category]


def find_artist_by_id(artist_id):
    for artist in BASE_ARTISTS:
        if artist.get("id") == artist_id:
            return artist
    return None


def get_artist_services(artist):
    if not artist:
        return []
    artist_id = artist.get("id")
    schedule = ARTIST_SCHEDULES.get(artist_id, {})
    if schedule.get("services"):
        return list(schedule["services"])
    return list(SUBCATEGORIES.get(artist.get("category"), []))


def get_artist_schedule(artist):
    if not artist:
        return dict(DEFAULT_ARTIST_SCHEDULE)
    result = dict(DEFAULT_ARTIST_SCHEDULE)
    result.update(ARTIST_SCHEDULES.get(artist.get("id"), {}))
    return result
