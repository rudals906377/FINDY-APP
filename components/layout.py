from typing import Optional

# Brand colors — official spec (메인/포인트), white base maintained
MAIN_COLOR = "#AE8F6F"
MAIN_COLOR_DARK = "#8B6B4F"
MAIN_COLOR_SOFT = "#F5EEE7"
SUB_COLOR = "#E6D7C8"

BG_COLOR = "#FFFFFF"
SURFACE_COLOR = "#FFFFFF"
CARD_COLOR = "#FFFFFF"

TEXT_COLOR = "#2C2A28"
TEXT_STRONG = "#1A1A1A"
SUBTEXT_COLOR = "#9A9189"
MUTED_TEXT_COLOR = "#BDB4AB"

CHIP_BG = "#F7F2EC"
BORDER_COLOR = "#ECE5DB"
DIVIDER_COLOR = "#F1ECE4"
INPUT_BG = "#FAF7F2"
CATEGORY_BOX_BG = "#FFFFFF"

# Device / layout
PHONE_WIDTH = 400
PHONE_HEIGHT = 800
NAV_BAR_HEIGHT = 62
NAV_SAFE_GAP = 28

CONTENT_WIDTH = 340
FIELD_WIDTH = 300
HALF_CARD_WIDTH = 160

# Spacing
SPACE_XXS = 2
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_2XL = 32

# Radius
RADIUS_SM = 10
RADIUS_MD = 16
RADIUS_LG = 22
RADIUS_XL = 28
RADIUS_2XL = 32
PILL_RADIUS = 999

# Snap / carousel legacy-compatible constants
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

# Category legacy-compatible constants
CATEGORY_SIZE = 78
CATEGORY_RADIUS = 16
CATEGORY_EMOJI_SIZE = 22
CATEGORY_TEXT_SIZE = 10
CATEGORY_BOX_PADDING = 12
CATEGORY_GAP = 8

# Assets / fonts
APP_FONT = "Pretendard"
APP_FONT_BOLD = "Pretendard-Bold"

OPENING_IMAGE = "findy_opening_logo.png"
LOGIN_BRAND_IMAGE = "findy_logo_vertical.png"
OPENING_DURATION = 2.2

# Shadow presets — softer, more diffuse for a calm beauty-app feel
SHADOW_SOFT = {
    "spread_radius": 0,
    "blur_radius": 14,
    "color": "#0A1A140E",
    "offset_x": 0,
    "offset_y": 2,
}

SHADOW_CARD = {
    "spread_radius": 0,
    "blur_radius": 22,
    "color": "#0E1A140E",
    "offset_x": 0,
    "offset_y": 5,
}

SHADOW_FLOATING = {
    "spread_radius": 0,
    "blur_radius": 32,
    "color": "#141A140E",
    "offset_x": 0,
    "offset_y": 8,
}

# Legacy-compatible alias
FLOATING_SHADOW = SHADOW_FLOATING

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
