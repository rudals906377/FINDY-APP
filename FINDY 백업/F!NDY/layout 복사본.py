from typing import Optional

# Brand palette
MAIN_COLOR = "#AE8F6F"
MAIN_COLOR_DARK = "#8F7154"
MAIN_COLOR_SOFT = "#F5EEE6"
BG_COLOR = "#F8F6F3"
SURFACE_COLOR = "#FFFFFF"
CARD_COLOR = SURFACE_COLOR
TEXT_COLOR = "#1F1A17"
TEXT_MUTED = "#756A62"
SUBTEXT_COLOR = TEXT_MUTED
CHIP_BG = "#FBF7F2"
BORDER_COLOR = "#E8DED3"
BORDER_SOFT = "#F1EAE2"
CATEGORY_BOX_BG = SURFACE_COLOR
OVERLAY_SCRIM = "#26000000"

# Device frame
PHONE_WIDTH = 400
PHONE_HEIGHT = 800
NAV_BAR_HEIGHT = 62
NAV_SAFE_GAP = 28

# Layout widths
CONTENT_WIDTH = 340
FIELD_WIDTH = 300
HALF_CARD_WIDTH = 160

# Spacing scale
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_2XL = 32

# Radius scale
RADIUS_SM = 10
RADIUS_MD = 16
RADIUS_LG = 24
RADIUS_XL = 28
RADIUS_2XL = 34

# Snap layout
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

# Category grid
CATEGORY_SIZE = 78
CATEGORY_RADIUS = 16
CATEGORY_EMOJI_SIZE = 22
CATEGORY_TEXT_SIZE = 10
CATEGORY_BOX_PADDING = 12
CATEGORY_GAP = 8

# Brand assets
OPENING_IMAGE = "findy_opening_screen.png"
LOGIN_BRAND_IMAGE = "findy_login_logo_transparent.png"
OPENING_DURATION = 2.2
APP_FONT = "Pretendard"

# Shared visual tokens
CARD_SHADOW = {
    "spread_radius": 0,
    "blur_radius": 18,
    "color": "#12000000",
    "offset_x": 0,
    "offset_y": 6,
}

FLOATING_SHADOW = {
    "spread_radius": 0,
    "blur_radius": 24,
    "color": "#16000000",
    "offset_x": 0,
    "offset_y": 10,
}

HAIRLINE_BORDER_OPACITY = 0.95


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
