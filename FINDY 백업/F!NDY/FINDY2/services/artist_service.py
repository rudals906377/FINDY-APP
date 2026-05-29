# 간단한 더미 데이터 기반 artist 서비스

ARTISTS = [
    {
        "id": 1,
        "name": "지우 디자이너",
        "job": "헤어 디자이너",
        "category": "헤어",
        "rating": 4.9,
        "distance": "1.2km",
        "price": "₩80,000~",
        "intro": "트렌디한 스타일과 섬세한 컷으로 인기 있는 디자이너",
        "style": "내추럴 / 트렌디",
        "reason": "고객 맞춤 스타일링",
    },
    {
        "id": 2,
        "name": "민서 메이크업",
        "job": "메이크업 아티스트",
        "category": "메이크업",
        "rating": 4.8,
        "distance": "2.1km",
        "price": "₩120,000~",
        "intro": "웨딩 및 데일리 메이크업 전문",
        "style": "내추럴 / 웨딩",
        "reason": "피부 표현이 뛰어남",
    },
    {
        "id": 3,
        "name": "하늘 네일",
        "job": "네일 아티스트",
        "category": "네일아트",
        "rating": 4.7,
        "distance": "0.8km",
        "price": "₩50,000~",
        "intro": "감성적인 컬러와 디자인 네일 전문",
        "style": "컬러 / 아트",
        "reason": "트렌디한 디자인",
    },
]


def list_artists(category=None):
    if not category or category == "전체":
        return ARTISTS
    return [a for a in ARTISTS if a["category"] == category]


def find_artist_by_id(artist_id):
    for a in ARTISTS:
        if a["id"] == artist_id:
            return a
    return None


def get_artist_services(artist):
    category = artist.get("category")

    if category == "헤어":
        return ["컷", "펌", "염색"]
    elif category == "메이크업":
        return ["데일리", "웨딩", "촬영"]
    elif category == "네일아트":
        return ["기본케어", "젤네일", "아트"]
    else:
        return ["기본 서비스"]


def get_artist_schedule(artist):
    return {
        "start": "10:00",
        "end": "20:00"
    }
