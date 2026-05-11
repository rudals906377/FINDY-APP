"""FINDY 플레이스홀더 이미지 생성 — 단색 단순 버전"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
FONT_BOLD = os.path.join(ASSETS, "Pretendard-Bold.ttf")
FONT_REG  = os.path.join(ASSETS, "Pretendard-Regular.ttf")
if not (os.path.exists(FONT_BOLD) and os.path.exists(FONT_REG)):
    FONT_BOLD = os.path.join(ASSETS, "Pretendard", "Pretendard-Bold.ttf")
    FONT_REG  = os.path.join(ASSETS, "Pretendard", "Pretendard-Regular.ttf")

GREEN     = (72, 160, 100)    # 메인 초록
GREEN_DRK = (48, 120, 72)     # 텍스트용 진한 초록
WHITE     = (255, 255, 255)


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def draw_centered(draw, text, fnt, cx, cy, color=WHITE):
    bb = draw.textbbox((0, 0), text, font=fnt)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((cx - w / 2, cy - h / 2), text, font=fnt, fill=color)


def make_solid(w, h, label_big, label_small=None, out_path=None):
    img = Image.new("RGB", (w, h), GREEN)
    draw = ImageDraw.Draw(img)

    # 테두리 안쪽 사각형 (약간 어두운 테)
    margin = 8
    draw.rectangle(
        [(margin, margin), (w - margin, h - margin)],
        outline=GREEN_DRK, width=2,
    )

    cx, cy = w // 2, h // 2

    f_big   = font(FONT_BOLD, max(20, min(48, w // 7)))
    f_small = font(FONT_REG,  max(14, min(22, w // 14)))

    if label_small:
        draw_centered(draw, label_big,   f_big,   cx, cy - 18)
        draw_centered(draw, label_small, f_small, cx, cy + 22)
    else:
        draw_centered(draw, label_big, f_big, cx, cy)

    img.save(out_path, "PNG")
    print(f"  ✓ {os.path.basename(out_path)}")


# ── 아티스트 프로필 400×400 ──────────────────────
ARTISTS = [
    ("a1", "민지 디자이너",  "헤어"),
    ("a2", "지훈 아티스트",  "메이크업"),
    ("a3", "수아 디자이너",  "네일아트"),
    ("a4", "도윤 아티스트",  "포토"),
    ("a5", "예린 디자이너",  "웨딩"),
    ("a6", "하준 아티스트",  "반영구"),
    ("a7", "서윤 디자이너",  "포토"),
    ("a8", "태민 아티스트",  "헤어"),
]

# ── 스냅 피드 400×500 ─────────────────────────
SNAPS = [
    ("s01", "레이어드 컷",    "헤어"),
    ("s02", "윤광 베이스",    "메이크업"),
    ("s03", "빌드펌 무드컷",  "헤어"),
    ("s04", "웨딩 피치",      "메이크업"),
    ("s05", "드라이 볼륨",    "헤어"),
    ("s06", "내추럴 브라운",  "헤어"),
    ("s07", "글로시 핑크",    "네일아트"),
    ("s08", "데일리 음영",    "메이크업"),
    ("s09", "화이트 프렌치",  "네일아트"),
    ("s10", "시크 블랙 단발", "헤어"),
    ("s11", "무드 파츠",      "네일아트"),
    ("s12", "봄 라이트",      "메이크업"),
    ("s13", "클라우드 시럽",  "네일아트"),
    ("s14", "로지 포인트",    "메이크업"),
    ("s15", "리본 포인트",    "네일아트"),
    ("s16", "감성 프로필",    "포토"),
    ("s17", "브라이드 무드",  "웨딩"),
    ("s18", "자연눈썹 시술",  "반영구"),
    ("s19", "데일리 무드",    "포토"),
    ("s20", "본식 헤어메이크업", "웨딩"),
    ("s21", "아이라인 포인트", "반영구"),
]

# ── 광고 배너 680×320 ─────────────────────────
BANNERS = [
    ("banner_1", "광고",   "맞춤 아티스트 찾기"),
    ("banner_2", "광고",   "신규 아티스트 20% 혜택"),
    ("banner_3", "광고",   "오늘 예약 가능한 아티스트"),
]


if __name__ == "__main__":
    print("▶ 아티스트 프로필 이미지 (400×400)...")
    for aid, name, cat in ARTISTS:
        make_solid(400, 400, name, cat,
                   os.path.join(ASSETS, f"artist_{aid}.png"))

    print("▶ 스냅 피드 이미지 (400×500)...")
    for sid, title, cat in SNAPS:
        make_solid(400, 500, title, cat,
                   os.path.join(ASSETS, f"snap_{sid}.png"))

    print("▶ 광고 배너 이미지 (680×320)...")
    for bid, big, small in BANNERS:
        make_solid(680, 320, big, small,
                   os.path.join(ASSETS, f"{bid}.png"))

    total = len(ARTISTS) + len(SNAPS) + len(BANNERS)
    print(f"\n완료: 총 {total}개 이미지 생성됨")
