from typing import Optional

MAIN_COLOR = "#AE8F6F"
BG_COLOR = "#FFFFFF"
CARD_COLOR = "#FFFFFF"
TEXT_COLOR = "#2F2F2F"
SUBTEXT_COLOR = "#8A8178"
CHIP_BG = "#FFFCF8"
BORDER_COLOR = "#E7DED4"
CATEGORY_BOX_BG = "#FFFFFF"

PHONE_WIDTH = 400
PHONE_HEIGHT = 800
NAV_BAR_HEIGHT = 62
NAV_SAFE_GAP = 28

CONTENT_WIDTH = 340
FIELD_WIDTH = 300
HALF_CARD_WIDTH = 160

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24

RADIUS_SM = 10
RADIUS_MD = 16
RADIUS_LG = 24
RADIUS_XL = 28

SNAP_CARD_WIDTH = 100
SNAP_CARD_WIDTH_FOCUSED = 112
SNAP_IMAGE_WIDTH = 100
SNAP_IMAGE_WIDTH_FOCUSED = 112
SNAP_IMAGE_HEIGHT = 132
SNAP_IMAGE_HEIGHT_FOCUSED = 146
SNAP_CARD_PADDING = 4
SNAP_CARD_PADDING_FOCUSED = 5
SNAP_CARD_SPACING = 2
SNAP_CAROUSEL_HEIGHT = 430
SNAP_FOLLOWING_SECTION_GAP = 24

CATEGORY_SIZE = 78
CATEGORY_RADIUS = 16
CATEGORY_EMOJI_SIZE = 22
CATEGORY_TEXT_SIZE = 10
CATEGORY_BOX_PADDING = 12
CATEGORY_GAP = 8

OPENING_IMAGE = "findy_opening_screen.png"
LOGIN_BRAND_IMAGE = "findy_login_logo_transparent.png"
OPENING_DURATION = 2.2
APP_FONT = "Pretendard"

def build_layout_metrics(page_width: Optional[float], phone_width: int = PHONE_WIDTH) -> dict:
    current_page_width = page_width or phone_width
    frame_width = min(phone_width, current_page_width) if current_page_width else phone_width
    content_width = min(CONTENT_WIDTH, max(280, frame_width - 60))
    field_width = min(FIELD_WIDTH, max(240, content_width - 40))
    half_card_width = max(132, int((content_width - SPACE_SM) / 2))
    return {
        "frame_width": frame_width,
        "content_width": content_width,
        "field_width": field_width,
        "half_card_width": half_card_width,
    }
