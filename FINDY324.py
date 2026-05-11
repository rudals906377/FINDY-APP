import asyncio
import json
import os
from datetime import date, datetime, timedelta
import calendar
from typing import Optional
import flet as ft

from data.artists import BASE_ARTISTS
from data.categories import LEFT_OVERLAY_CATEGORIES, LEFT_OVERLAY_ICONS, SUBCATEGORIES
from data.reviews import REVIEW_ITEMS
from data.snaps import SNAP_ITEMS

from components.layout import (
    APP_FONT,
    BG_COLOR,
    BORDER_COLOR,
    CARD_COLOR,
    CATEGORY_BOX_BG,
    CATEGORY_BOX_PADDING,
    CATEGORY_EMOJI_SIZE,
    CATEGORY_GAP,
    CATEGORY_RADIUS,
    CATEGORY_SIZE,
    CATEGORY_TEXT_SIZE,
    CHIP_BG,
    CONTENT_WIDTH,
    FIELD_WIDTH,
    HALF_CARD_WIDTH,
    LOGIN_BRAND_IMAGE,
    MAIN_COLOR,
    MAIN_COLOR_DARK,
    MAIN_COLOR_SOFT,
    NAV_BAR_HEIGHT,
    NAV_SAFE_GAP,
    OPENING_DURATION,
    OPENING_IMAGE,
    PHONE_HEIGHT,
    PHONE_WIDTH,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_SM,
    RADIUS_XL,
    SNAP_CARD_PADDING,
    SNAP_CARD_PADDING_FOCUSED,
    SNAP_CARD_SPACING,
    SNAP_CARD_WIDTH,
    SNAP_CARD_WIDTH_FOCUSED,
    SNAP_CAROUSEL_HEIGHT,
    SNAP_FOLLOWING_SECTION_GAP,
    SNAP_IMAGE_HEIGHT,
    SNAP_IMAGE_HEIGHT_FOCUSED,
    SNAP_IMAGE_WIDTH,
    SNAP_IMAGE_WIDTH_FOCUSED,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SPACE_XL,
    SUBTEXT_COLOR,
    TEXT_COLOR,
    build_layout_metrics,
)
from components.cards import (
    browse_result_card as ui_browse_result_card,
    page_header as ui_page_header,
    review_card as ui_review_card,
    section_title as ui_section_title,
    soft_button as ui_soft_button,
)
from components.overlays import (
    build_left_overlay as ui_build_left_overlay,
    build_right_overlay as ui_build_right_overlay,
)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
RESERVATION_STORAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reservation_history.json")

async def main(page: ft.Page):

    def safe_go_back(e=None):
        try:
            show_home_page()
        except Exception:
            pass
    def resolve_asset_file(name: str) -> Optional[str]:
        candidates = [
            name,
            name + ".png" if not name.lower().endswith(".png") else name + ".png",
            name[:-4] if name.lower().endswith(".png.png") else None,
        ]
        cleaned = []
        for item in candidates:
            if item and item not in cleaned:
                cleaned.append(item)

        search_dirs = [
            ASSETS_DIR,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
            os.path.join(os.getcwd(), "assets"),
        ]
        for folder in search_dirs:
            for candidate in cleaned:
                path = os.path.join(folder, candidate)
                if os.path.exists(path):
                    return path
        return None

    def layout_metrics():
        page_width = getattr(page, "width", None) or PHONE_WIDTH
        frame_width = min(PHONE_WIDTH, page_width) if page_width else PHONE_WIDTH
        content_width = min(CONTENT_WIDTH, max(280, frame_width - 60))
        field_width = min(FIELD_WIDTH, max(240, content_width - 40))
        half_card_width = max(132, int((content_width - SPACE_SM) / 2))
        return {
            "frame_width": frame_width,
            "content_width": content_width,
            "field_width": field_width,
            "half_card_width": half_card_width,
        }

    def content_width():
        return layout_metrics()["content_width"]

    def field_width():
        return layout_metrics()["field_width"]

    def half_card_width():
        return layout_metrics()["half_card_width"]

    def full_phone_width():
        return layout_metrics()["frame_width"]

    def build_standard_header(title, on_back=None, on_close=None, width=None):
        return ui_page_header(title, on_back=on_back, width=width or content_width())

    def page_header(title, on_back=None, width=None):
        return ui_page_header(title, on_back=on_back, width=width or content_width())

    def page_title_map():
        current_page = app_state.get("current_page", "")
        mapping = {
            "snap": "스냅",
            "video": "비디오",
            "my": "내정보",
            "saved": "저장한 뷰티",
            "detail": "아티스트",
            "reservation": "예약",
            "reservation_confirm": "예약 확인",
            "reservation_complete": "예약 완료",
            "reservation_history": "예약내역",
            "notifications": "알림",
            "review": "리뷰",
            "search": "검색",
            "search_results": "전체 보기",
            "snap_detail": "스냅",
            "support": "고객센터",
            "inquiry": "문의내역",
            "completed": "완료한 시술",
            "cancelled_treatments": "취소된 시술",
            "beauty_profile": "나의 뷰티 정보",
            "notice": "공지사항",
            "feedback": "개선 의견",
            "placeholder_info": "안내",
        }
        return mapping.get(current_page, "")

    def section_title(title, subtitle=None, on_click=None):
        return ui_section_title(title, subtitle=subtitle, on_click=on_click, width=content_width())

    def soft_button(label, bgcolor, text_color, on_click, border=None, width=None):
        return ui_soft_button(label, bgcolor, text_color, on_click, border=border, width=width or field_width())

    def review_card(name, category, review, photos=None, rating=5):
        return ui_review_card(name, category, review, width=content_width(), photos=photos, rating=rating)

    def browse_result_card(item, on_click=None):
        return ui_browse_result_card(item, width=content_width(), on_click=on_click)

    def opening_visual():
        path = resolve_asset_file(OPENING_IMAGE)
        if path:
            return ft.Image(
                src=path,
                width=full_phone_width(),
                height=PHONE_HEIGHT,
                fit="contain",
                opacity=0,
                animate_opacity=ft.Animation(420, ft.AnimationCurve.EASE_IN_OUT),
            )
        return ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            alignment=ft.Alignment(0, 0),
            content=brand_logo(show_slogan=True),
        )

    def login_logo_visual():
        path = resolve_asset_file(LOGIN_BRAND_IMAGE)
        if path:
            return ft.Image(
                src=path,
                width=176,
                fit="contain",
            )
        return brand_logo(show_slogan=False, compact=False)

    page.title = "FINDY324"
    regular_font_rel = "assets/Pretendard-Regular.ttf"
    bold_font_rel = "assets/Pretendard-Bold.ttf"
    regular_font = os.path.join(ASSETS_DIR, "Pretendard-Regular.ttf")
    bold_font = os.path.join(ASSETS_DIR, "Pretendard-Bold.ttf")
    if not (os.path.exists(regular_font) and os.path.exists(bold_font)):
        regular_font_rel = "assets/Pretendard/Pretendard-Regular.ttf"
        bold_font_rel = "assets/Pretendard/Pretendard-Bold.ttf"
        regular_font = os.path.join(ASSETS_DIR, "Pretendard", "Pretendard-Regular.ttf")
        bold_font = os.path.join(ASSETS_DIR, "Pretendard", "Pretendard-Bold.ttf")
    if os.path.exists(regular_font) and os.path.exists(bold_font):
        page.fonts = {
            "Pretendard": regular_font_rel,
            "Pretendard-Bold": bold_font_rel,
        }
        page.theme = ft.Theme(font_family="Pretendard")
    else:
        page.theme = ft.Theme()
    page.window.width = 520
    page.window.height = 920
    page.padding = 0
    page.bgcolor = BG_COLOR
    page.scroll = ft.ScrollMode.HIDDEN
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.font_family = APP_FONT if os.path.exists(regular_font) else None

    app_state = {
        "saved_ids": set(),
        "selected_tab": 0,
        "selected_category": None,
        "search_text": "",
        "search_results": [],
        "search_sort": "rating",
        "recommendation_entry": None,
        "detail_artist": None,
        "detail_back_target": "home",
        "ad_index": 0,
        "ad_task_started": False,
        "snap_index": 0,
        "snap_task_started": False,
        "snap_cards_row": None,
        "review_index": 0,
        "review_cards_column": None,
        "overlay": None,  # None | "left" | "right"
        "left_menu_expanded": None,
        "snap_layout_mode": 3,
        "snap_sort_mode": "popular",
        "snap_filter": "헤어",
        "snap_detail_item": None,
        "snap_liked_ids": set(),
        "snap_saved_ids": set(),
        "written_snaps": [],
        "community_posts": [],
        "written_videos": [],
        "video_category_filter": "전체",
        "current_user": None,
        "reservation_form": {
            "artist_id": None,
            "artist_name": "",
            "job": "",
            "category": "",
            "date": None,
            "time": None,
            "note": "",
        },
        "reservation_history": [],
        "written_reviews": [],
        "review_target": None,
        "last_completed_reservation": None,
        "reservation_month_offset": 0,
        "dismissed_upcoming_notice_id": None,
        "notification_read_at": None,
        "inquiry_history": [],
        "inquiry_draft": {
            "category": "예약/결제",
            "title": "",
            "content": "",
        },
        "my_info_expanded_sections": set(),
        "page_history": [],
        "_last_rendered_page": None,
    }
    subcategories = SUBCATEGORIES

    left_overlay_categories = LEFT_OVERLAY_CATEGORIES

    left_overlay_icons = LEFT_OVERLAY_ICONS

    base_artists = BASE_ARTISTS

    def app_icon(*names):
        for name in names:
            if hasattr(ft.Icons, name):
                return getattr(ft.Icons, name)
        return ft.Icons.CIRCLE

    def brand_mark(size=92):
        path = resolve_asset_file("findy_logo_mark.png")
        if path:
            return ft.Image(
                src=path,
                width=size,
                height=size * 0.56,
                fit=ft.ImageFit.CONTAIN,
            )

        frame = MAIN_COLOR
        pupil = "#B37433"

        ring = lambda: ft.Container(
            width=size * 0.42,
            height=size * 0.42,
            border=ft.border.all(max(3, int(size * 0.055)), frame),
            border_radius=999,
            content=ft.Container(
                width=size * 0.12,
                height=size * 0.12,
                bgcolor=pupil,
                border_radius=999,
                alignment=ft.Alignment(0, 0),
            ),
            alignment=ft.Alignment(0, 0),
        )

        return ft.Container(
            width=size,
            height=size * 0.56,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0.18),
                        content=ft.Row(
                            controls=[ring(), ring()],
                            spacing=size * 0.06,
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, -0.28),
                        content=ft.Container(
                            width=size * 0.16,
                            height=size * 0.08,
                            bgcolor=frame,
                            border_radius=999,
                        ),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, -0.02),
                        content=ft.Container(
                            width=size * 0.12,
                            height=size * 0.22,
                            bgcolor=frame,
                            border_radius=999,
                        ),
                    ),
                ]
            ),
        )

    def brand_logo(show_slogan=False, compact=False):
        image_name = "findy_logo_vertical.png" if show_slogan else "findy_logo_horizontal.png"
        path = resolve_asset_file(image_name)
        if path:
            return ft.Image(
                src=path,
                width=188 if not compact else 142,
                fit=ft.ImageFit.CONTAIN,
            )
        return ft.Column(
            controls=[
                brand_mark(96 if not compact else 70),
                ft.Text(
                    "FINDY",
                    size=40 if not compact else 28,
                    weight=ft.FontWeight.BOLD,
                    font_family="Pretendard-Bold",
                    color=MAIN_COLOR,
                ),
                ft.Text(
                    "Find Your Beauty",
                    size=14 if not compact else 12,
                    color=MAIN_COLOR,
                ) if show_slogan else ft.Container(),
            ],
            spacing=4 if not compact else 2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def find_artist_by_id(artist_id):
        for artist in base_artists:
            if artist["id"] == artist_id:
                return artist
        return None

    def toggle_saved(artist_id):
        if artist_id in app_state["saved_ids"]:
            app_state["saved_ids"].remove(artist_id)
        else:
            app_state["saved_ids"].add(artist_id)

    def is_saved(artist_id):
        return artist_id in app_state["saved_ids"]

    def show_snack(message, bgcolor=None):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=bgcolor or MAIN_COLOR,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        page.snack_bar.open = True
        page.update()

    def black_image_box(width, height, border_radius=0):
        return ft.Container(
            width=width,
            height=height,
            bgcolor="#000000",
            border_radius=border_radius,
        )

    def ad_banner():
        _banner_files = ["assets/banner_1.png", "assets/banner_2.png", "assets/banner_3.png"]
        _n = len(_banner_files)

        banner_img = black_image_box(content_width(), 160)

        dot_row = ft.Row(
            controls=[
                ft.Container(
                    width=7 if i == app_state["ad_index"] else 5,
                    height=5,
                    border_radius=3,
                    bgcolor="#FFFFFF" if i == app_state["ad_index"] else ft.Colors.with_opacity(0.45, "#FFFFFF"),
                )
                for i in range(_n)
            ],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        def refresh():
            idx = app_state["ad_index"]
            for i, dot in enumerate(dot_row.controls):
                dot.width = 7 if i == idx else 5
                dot.bgcolor = "#FFFFFF" if i == idx else ft.Colors.with_opacity(0.45, "#FFFFFF")
            page.update()

        def prev_ad(e):
            app_state["ad_index"] = (app_state["ad_index"] - 1) % _n
            refresh()

        def next_ad(e):
            app_state["ad_index"] = (app_state["ad_index"] + 1) % _n
            refresh()

        async def auto_slide():
            while True:
                await asyncio.sleep(3.5)
                if app_state["selected_tab"] == 2:
                    app_state["ad_index"] = (app_state["ad_index"] + 1) % _n
                    refresh()

        if not app_state["ad_task_started"]:
            app_state["ad_task_started"] = True
            page.run_task(auto_slide)

        return ft.Container(
            width=content_width(),
            height=160,
            border_radius=30,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#22000000",
                offset=ft.Offset(0, 8),
            ),
            content=ft.Stack(
                controls=[
                    banner_img,
                    ft.Container(
                        left=0, top=0, bottom=0,
                        alignment=ft.Alignment(-1, 0),
                        content=ft.IconButton(
                            icon=app_icon("CHEVRON_LEFT", "ARROW_BACK_IOS_NEW", "ARROW_BACK"),
                            icon_color="white",
                            on_click=prev_ad,
                        ),
                    ),
                    ft.Container(
                        right=0, top=0, bottom=0,
                        alignment=ft.Alignment(1, 0),
                        content=ft.IconButton(
                            icon=app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"),
                            icon_color="white",
                            on_click=next_ad,
                        ),
                    ),
                    ft.Container(
                        bottom=10,
                        left=0, right=0,
                        alignment=ft.Alignment(0, 1),
                        content=dot_row,
                    ),
                ]
            ),
        )

    def close_overlays():
        app_state["overlay"] = None

    def open_overlay(name: str):
        app_state["overlay"] = name

    def is_overlay_open(name: str) -> bool:
        return app_state.get("overlay") == name

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
            "blocked_dates": [(date.today() + timedelta(days=5)).strftime("%Y-%m-%d")],
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

    def get_artist_services(artist=None):
        artist = artist or get_reservation_artist() or {}
        schedule = get_artist_schedule(artist)
        if schedule.get("services"):
            return list(schedule.get("services") or [])
        category = artist.get("category") or ""
        return list(subcategories.get(category, []))

    def get_artist_schedule(artist=None):
        artist = artist or get_reservation_artist() or {}
        schedule = dict(DEFAULT_ARTIST_SCHEDULE)
        artist_schedule = ARTIST_SCHEDULES.get(artist.get("id"), {})
        schedule.update(artist_schedule)
        schedule["breaks"] = list(artist_schedule.get("breaks", schedule.get("breaks", [])))
        schedule["off_weekdays"] = list(artist_schedule.get("off_weekdays", schedule.get("off_weekdays", [])))
        schedule["blocked_dates"] = list(artist_schedule.get("blocked_dates", schedule.get("blocked_dates", [])))
        schedule["services"] = list(artist_schedule.get("services", schedule.get("services") or []) or [])
        return schedule

    def generate_reservation_slots(artist=None):
        schedule = get_artist_schedule(artist)
        slot_minutes = max(10, int(schedule.get("slot_minutes", 30) or 30))
        current_slot = datetime.strptime(schedule.get("start", "09:00"), "%H:%M")
        slot_end = datetime.strptime(schedule.get("end", "22:00"), "%H:%M")
        slots = []
        while current_slot <= slot_end:
            slots.append(current_slot.strftime("%H:%M"))
            current_slot += timedelta(minutes=slot_minutes)
        return slots

    def is_artist_off_day(artist, date_value):
        if not artist or not date_value:
            return False
        try:
            target_date = datetime.strptime(date_value, "%Y-%m-%d").date()
        except Exception:
            return False
        schedule = get_artist_schedule(artist)
        return target_date.weekday() in set(schedule.get("off_weekdays", []))

    def is_artist_blocked_date(artist, date_value):
        if not artist or not date_value:
            return False
        schedule = get_artist_schedule(artist)
        return date_value in set(schedule.get("blocked_dates", []))

    def get_artist_booking_limit_date(artist):
        schedule = get_artist_schedule(artist)
        booking_days = max(7, int(schedule.get("booking_days", 45) or 45))
        return date.today() + timedelta(days=booking_days)

    def is_date_selectable_for_artist(artist, target_date):
        if not artist or not target_date:
            return False
        if target_date < date.today():
            return False
        if target_date > get_artist_booking_limit_date(artist):
            return False
        date_value = target_date.strftime("%Y-%m-%d")
        if is_artist_off_day(artist, date_value):
            return False
        if is_artist_blocked_date(artist, date_value):
            return False
        return True

    def get_day_cell_state(artist, target_date):
        if not target_date:
            return "disabled"
        if target_date < date.today():
            return "past"
        if target_date > get_artist_booking_limit_date(artist):
            return "out_of_range"
        date_value = target_date.strftime("%Y-%m-%d")
        if is_artist_blocked_date(artist, date_value):
            return "blocked"
        if is_artist_off_day(artist, date_value):
            return "off_day"
        return "available"

    def is_break_time(artist, time_value):
        if not artist or not time_value:
            return False
        schedule = get_artist_schedule(artist)
        for start_value, end_value in schedule.get("breaks", []):
            if start_value <= time_value < end_value:
                return True
        return False

    def get_time_slot_state(artist, date_value, time_value):
        if not date_value:
            return "need_date"
        if is_artist_blocked_date(artist, date_value):
            return "blocked"
        if is_artist_off_day(artist, date_value):
            return "off_day"
        if is_time_already_booked(artist["id"], date_value, time_value):
            return "booked"
        if is_time_past(date_value, time_value):
            return "past"
        if is_break_time(artist, time_value):
            return "break"
        return "available"

    def reset_reservation_form(artist=None):
        services = get_artist_services(artist) if artist else []
        app_state["reservation_month_offset"] = 0
        app_state["reservation_form"] = {
            "artist_id": artist["id"] if artist else None,
            "artist_name": artist["name"] if artist else "",
            "job": artist["job"] if artist else "",
            "category": artist["category"] if artist else "",
            "service": services[0] if services else "기본 시술",
            "date": None,
            "time": None,
            "note": "",
        }

    def get_reservation_form():
        form = app_state.get("reservation_form")
        if not form:
            reset_reservation_form()
            form = app_state["reservation_form"]
        return form

    def get_reservation_artist():
        form = get_reservation_form()
        artist_id = form.get("artist_id")
        if artist_id:
            artist = find_artist_by_id(artist_id)
            if artist:
                return artist
        return app_state.get("detail_artist")

    def reservation_datetime(date_value, time_value):
        if not date_value or not time_value:
            return None
        try:
            return datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
        except Exception:
            return None

    def is_time_past(date_value, time_value):
        dt = reservation_datetime(date_value, time_value)
        if not dt:
            return False
        return dt < datetime.now()

    def format_reservation_date_text(date_value, time_value=None):
        dt = reservation_datetime(date_value, time_value or "00:00")
        if not dt:
            return date_value or ""
        weekday = ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()]
        period = "오전" if dt.hour < 12 else "오후"
        hour_12 = dt.hour % 12 or 12
        if time_value:
            return f"{dt.month}월 {dt.day}일({weekday}) {period} {hour_12}:{dt.minute:02d}"
        return f"{dt.month}월 {dt.day}일({weekday})"

    def build_reservation_countdown_text(date_value, time_value):
        dt = reservation_datetime(date_value, time_value)
        if not dt:
            return ""
        now_dt = datetime.now()
        delta = dt - now_dt
        total_minutes = int(delta.total_seconds() // 60)
        if total_minutes < 0:
            return "지난 예약"
        if dt.date() == now_dt.date():
            if total_minutes < 60:
                return f"{max(1, total_minutes)}분 후"
            return f"{max(1, total_minutes // 60)}시간 후"
        if dt.date() == now_dt.date() + timedelta(days=1):
            return "내일"
        days_left = (dt.date() - now_dt.date()).days
        return f"D-{days_left}"

    def normalize_reservation_history_item(item):
        normalized = dict(item or {})
        if normalized.get("status") == "예약 요청 완료":
            normalized["status"] = "예약 완료"
        if not normalized.get("service"):
            normalized["service"] = normalized.get("category") or "기본 시술"
        return normalized

    def is_reservation_active(item):
        return item.get("status") not in {"예약 취소", "시술 완료", "노쇼"}

    def get_reservation_status_meta(status):
        mapping = {
            "예약 완료": (MAIN_COLOR, "예약 확정"),
            "예약 취소": ("#B85C5C", "취소됨"),
            "노쇼": ("#A15B43", "노쇼"),
            "시술 완료": ("#4F8A5B", "방문 완료"),
        }
        return mapping.get(status, (SUBTEXT_COLOR, status or "상태 없음"))

    def is_time_already_booked(artist_id, date_value, time_value, exclude_reservation_id=None):
        for item in app_state.get("reservation_history", []):
            if exclude_reservation_id and item.get("id") == exclude_reservation_id:
                continue
            if not is_reservation_active(item):
                continue
            if (
                item.get("artist_id") == artist_id
                and item.get("date") == date_value
                and item.get("time") == time_value
            ):
                return True
        return False

    def build_reservation_item_from_form():
        form = get_reservation_form().copy()
        return {
            "id": f'r{len(app_state.get("reservation_history", [])) + 1}',
            "artist_id": form.get("artist_id"),
            "artist_name": form.get("artist_name", ""),
            "job": form.get("job", ""),
            "category": form.get("category", ""),
            "service": form.get("service", "기본 시술"),
            "date": form.get("date"),
            "time": form.get("time"),
            "note": form.get("note", ""),
            "status": "예약 완료",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    def save_reservation_history_to_file():
        try:
            with open(RESERVATION_STORAGE_PATH, "w", encoding="utf-8") as f:
                json.dump(app_state.get("reservation_history", []), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save reservation history: {e}")

    def load_reservation_history_from_file():
        if not os.path.exists(RESERVATION_STORAGE_PATH):
            return []
        try:
            with open(RESERVATION_STORAGE_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                return [normalize_reservation_history_item(item) for item in loaded]
        except Exception as e:
            print(f"Failed to load reservation history: {e}")
        return []

    def cancel_reservation(reservation_id):
        for item in app_state.get("reservation_history", []):
            if item.get("id") == reservation_id:
                item["status"] = "예약 취소"
                item["cancelled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_reservation_history_to_file()
                return item
        return None

    def save_reservation():
        form = get_reservation_form()
        artist_id = form.get("artist_id")
        date_value = form.get("date")
        time_value = form.get("time")

        if not artist_id or not date_value or not time_value:
            show_snack("예약 정보를 다시 확인해주세요.", bgcolor="#B85C5C")
            return None

        artist = find_artist_by_id(artist_id)
        if artist and is_artist_blocked_date(artist, date_value):
            show_snack("해당 날짜는 예약이 열려 있지 않아요.", bgcolor="#B85C5C")
            return None

        if artist and is_artist_off_day(artist, date_value):
            show_snack("휴무일에는 예약할 수 없어요.", bgcolor="#B85C5C")
            return None

        if is_time_past(date_value, time_value):
            show_snack("지난 시간은 예약할 수 없어요.", bgcolor="#B85C5C")
            return None

        if is_time_already_booked(artist_id, date_value, time_value):
            show_snack("이미 예약이 마감된 시간이에요.", bgcolor="#B85C5C")
            return None

        reservation_item = build_reservation_item_from_form()
        history = app_state.setdefault("reservation_history", [])
        history.append(reservation_item)
        app_state["last_completed_reservation"] = reservation_item
        save_reservation_history_to_file()
        return reservation_item
    # Initialize reservation history from file (after helpers are defined)
    try:
        app_state["reservation_history"] = load_reservation_history_from_file()
    except Exception:
        app_state["reservation_history"] = []

    def clear_transient_ui():
        try:
            page.dialog = None
        except Exception:
            pass
        try:
            page.overlay.clear()
        except Exception:
            pass

    def go_back_page(e=None):
        try:
            if getattr(page, "dialog", None):
                page.dialog.open = False
                page.update()
                return
        except Exception:
            pass

        if app_state.get("overlay"):
            close_overlays()
            render_current_page()
            return

        clear_transient_ui()
        history = app_state.get("page_history", [])
        while history:
            previous_page = history.pop()
            if previous_page and previous_page != app_state.get("current_page"):
                app_state["current_page"] = previous_page
                if previous_page == "home":
                    app_state["selected_tab"] = 2
                elif previous_page == "snap":
                    app_state["selected_tab"] = 1
                elif previous_page == "video":
                    app_state["selected_tab"] = 3
                elif previous_page in {"my", "saved", "reservation_history", "cancelled_treatments", "placeholder_info"}:
                    app_state["selected_tab"] = 4
                render_current_page()
                return

        app_state["current_page"] = "home"
        app_state["selected_tab"] = 2
        show_home_page()

    def render_current_page():
        page_name = app_state.get("current_page", "home")
        if page_name == "category":
            show_category_page()
        elif page_name == "snap":
            show_snap_page()
        elif page_name == "search":
            show_search_page()
        elif page_name == "search_results":
            show_search_results_page()
        elif page_name == "my":
            show_my_page()
        elif page_name == "saved":
            show_saved_page()
        elif page_name == "detail":
            show_detail_page()
        elif page_name == "reservation_history":
            show_reservation_history_page()
        elif page_name == "cancelled_treatments":
            show_cancelled_treatments_page()
        elif page_name == "my_reviews":
            show_my_reviews_page()
        elif page_name == "review":
            show_review_page()
        elif page_name == "write_review":
            show_write_review_page()
        elif page_name == "video":
            show_video_page()
        elif page_name == "snap_detail":
            show_snap_detail_page()
        elif page_name == "write_snap":
            show_write_snap_page()
        elif page_name == "write_community":
            show_write_community_page()
        elif page_name == "write_video":
            show_write_video_page()
        elif page_name == "reservation":
            show_reservation_page()
        elif page_name == "reservation_confirm":
            show_reservation_confirm_page()
        elif page_name == "reservation_complete":
            show_reservation_complete_page()
        elif page_name == "notifications":
            show_notification_page()
        elif page_name == "support":
            show_support_page()
        elif page_name == "inquiry":
            show_inquiry_page()
        elif page_name == "completed":
            show_completed_page()
        elif page_name == "beauty_profile":
            show_beauty_profile_page()
        elif page_name == "notice":
            show_notice_page()
        elif page_name == "feedback":
            show_feedback_page()
        elif page_name == "placeholder_info":
            show_placeholder_info_page()
        else:
            show_home_page()

    def go_category_page(e=None):
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 0
        app_state["current_page"] = "category"
        show_category_page()

    def go_snap_page(e=None):
        close_overlays()
        app_state["selected_tab"] = 1
        app_state["current_page"] = "snap"
        show_snap_page()

    def go_home_page(e=None):
        close_overlays()
        app_state["selected_tab"] = 2
        app_state["current_page"] = "home"
        show_home_page()

    def go_video_page(e=None):
        close_overlays()
        app_state["selected_tab"] = 3
        app_state["current_page"] = "video"
        show_video_page()

    def go_my_page(e=None):
        clear_transient_ui()
        close_overlays()
        if app_state.get("current_page") != "my":
            app_state["my_scroll_offset"] = 0
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my"
        show_my_page()

    def open_left_menu(e=None):
        go_category_page(e)

    def open_right_menu(e=None):
        go_my_page(e)

    def normalize_overlay_category_name(category_name):
        return "반영구시술" if category_name == "반영구" else category_name

    def matches_query(query, *values):
        haystack = " ".join(str(value or "") for value in values).lower()
        return query.lower() in haystack

    def build_global_search_results(query):
        query = (query or "").strip()
        if not query:
            return []

        results = []

        for artist in base_artists:
            if matches_query(
                query,
                artist.get("name"),
                artist.get("category"),
                artist.get("job"),
                artist.get("style"),
                artist.get("reason"),
                artist.get("intro"),
                " ".join(artist.get("tags", [])),
            ):
                results.append({
                    "type": "artist",
                    "artist_id": artist["id"],
                    "title": artist["name"],
                    "subtitle": artist["job"],
                    "meta": f"⭐ {artist['rating']} · {artist['distance']} · {artist['price']}",
                    "description": artist["intro"],
                    "badge": "아티스트",
                })

        for category_name, items in subcategories.items():
            if matches_query(query, category_name, " ".join(items)):
                results.append({
                    "type": "category",
                    "title": category_name,
                    "subtitle": "카테고리",
                    "meta": "프롬프트 검색으로 바로 추천받을 수 있어요.",
                    "description": f"{category_name} 관련 스타일, 샵, 아티스트 정보를 찾아볼 수 있어요.",
                    "badge": "카테고리",
                })

        all_snap_items = []
        for category_name in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]:
            all_snap_items.extend(get_snap_feed_items("latest", category_name))
        for item in all_snap_items:
            if matches_query(query, item.get("title"), item.get("category")):
                results.append({
                    "type": "snap",
                    "snap_id": item["id"],
                    "title": item["title"],
                    "subtitle": item["category"],
                    "meta": f"좋아요 {item['likes']} · 저장 {item['saves']} · 조회 {item['views']}",
                    "description": f"{item['category']} 스타일 스냅 콘텐츠예요.",
                    "badge": "스냅",
                })

        for title, desc, emoji in get_snap_items():
            if matches_query(query, title, desc):
                results.append({
                    "type": "snap_collection",
                    "title": title,
                    "subtitle": "스냅 컬렉션",
                    "meta": emoji,
                    "description": desc,
                    "badge": "스냅",
                })

        for name, category, review in get_review_items():
            if matches_query(query, name, category, review):
                results.append({
                    "type": "review",
                    "title": f"{name}님의 리뷰",
                    "subtitle": category,
                    "meta": "실제 사용자 리뷰",
                    "description": review,
                    "badge": "리뷰",
                })

        for item in app_state.get("reservation_history", []):
            if matches_query(
                query,
                item.get("artist_name"),
                item.get("job"),
                item.get("category"),
                item.get("service"),
                item.get("status"),
                item.get("date"),
                item.get("time"),
                item.get("note"),
            ):
                results.append({
                    "type": "reservation",
                    "title": item.get("artist_name", "예약"),
                    "subtitle": item.get("service") or item.get("category") or "예약내역",
                    "meta": f"{item.get('date', '')} {item.get('time', '')} · {item.get('status', '')}",
                    "description": item.get("note") or "예약 히스토리에 저장된 정보예요.",
                    "badge": "예약",
                })

        return results

    def submit_global_search(query):
        query = (query or "").strip()
        if not query:
            show_snack("검색어를 입력해주세요.", bgcolor="#B85C5C")
            return

        app_state["search_text"] = query
        app_state["selected_category"] = None
        app_state["selected_subcategory"] = "통합검색"
        app_state["search_results"] = build_global_search_results(query)
        app_state["recommendation_entry"] = query
        app_state["category_browse_mode"] = True
        app_state["search_results_back_target"] = "home"
        app_state["selected_tab"] = 2
        app_state["current_page"] = "search_results"
        show_search_results_page()

    def build_category_browse_items(main_category, sub_category):
        normalized_category = normalize_overlay_category_name(main_category)
        category_artists = [a.copy() for a in base_artists if a["category"] == normalized_category]

        if sub_category == "아티스트":
            return category_artists

        if sub_category == "샵":
            shop_suffix_map = {
                "헤어": "헤어 스튜디오",
                "네일아트": "네일 스튜디오",
                "포토": "포토 스튜디오",
                "웨딩": "웨딩 살롱",
                "반영구": "브로우 스튜디오",
                "반영구시술": "브로우 스튜디오",
                "메이크업": "메이크업 스튜디오",
            }
            distance_seed = ["0.7km", "1.2km", "2.0km", "2.8km", "3.4km"]
            result = []
            for idx, artist in enumerate(category_artists):
                first_name = artist["name"].split()[0]
                result.append({
                    "type": "shop",
                    "title": f"{first_name} {shop_suffix_map.get(normalized_category, '뷰티 스튜디오')}",
                    "subtitle": f"{normalized_category} 전문 샵",
                    "meta": f"⭐ {artist['rating']} · {distance_seed[idx % len(distance_seed)]} · {artist['price']}",
                    "description": f"{artist['intro']} 상담 예약과 포트폴리오 확인이 가능한 등록 샵이에요.",
                    "badge": "샵",
                })
            return result

        if "스냅" in sub_category:
            mood_map = {
                "헤어": ["레이어드컷 전후", "내추럴 펌 무드", "컬러 체인지 스냅", "드라이 스타일링 컷"],
                "네일아트": ["이달의 네일", "웨딩 네일 무드", "파츠 아트 샘플", "깔끔한 젤네일"],
                "포토": ["데일리 스냅", "프로필 촬영", "감성 자연광 컷", "컨셉 포토 샘플"],
                "웨딩": ["본식 헤어메이크업", "하객 스타일링", "드레스 피팅 무드", "웨딩 스냅 하이라이트"],
                "반영구시술": ["자연눈썹 전후", "입술 컬러 시술", "아이라인 사례", "헤어라인 보정 사례"],
                "메이크업": ["데일리 메이크업", "화보 메이크업", "면접 메이크업", "웨딩 하객 메이크업"],
            }
            return [
                {
                    "type": "snap",
                    "title": title,
                    "subtitle": f"{main_category} 스타일 샘플",
                    "meta": f"조회 {1200 + idx * 230}",
                    "description": f"등록된 {main_category} 작업 이미지와 분위기를 한눈에 볼 수 있는 콘텐츠예요.",
                    "badge": "스냅",
                }
                for idx, title in enumerate(mood_map.get(normalized_category, [f"{main_category} 스냅 {i}" for i in range(1, 5)]), start=1)
            ]

        if sub_category == "리뷰":
            review_templates = [
                "상담이 꼼꼼하고 원하는 분위기를 정확하게 잡아줬어요.",
                "시술 결과가 자연스럽고 매장 분위기도 편안했어요.",
                "예약부터 마무리까지 응대가 친절해서 만족했어요.",
                "다음에도 같은 카테고리로 다시 방문하고 싶은 곳이에요.",
            ]
            result = []
            for idx, artist in enumerate(category_artists):
                result.append({
                    "type": "review",
                    "title": f"{artist['name']} 리뷰",
                    "subtitle": artist["job"],
                    "meta": f"⭐ {artist['rating']} · 방문자 리뷰",
                    "description": review_templates[idx % len(review_templates)],
                    "badge": "리뷰",
                })
            return result

        if sub_category == "커뮤니티":
            user_posts = [
                post.copy()
                for post in app_state.get("community_posts", [])
                if normalize_overlay_category_name(post.get("category")) == normalized_category
            ]
            topics = ["추천 부탁드려요", "전후 사진 공유", "가격대 궁금해요", "첫 방문 리뷰"]
            default_posts = [
                {
                    "type": "community",
                    "title": f"[{main_category}] {topic}",
                    "subtitle": "커뮤니티 게시글",
                    "meta": f"댓글 {idx + 3} · 저장 {idx + 8}",
                    "description": f"{main_category} 카테고리를 둘러보는 사용자들이 남긴 실시간 이야기예요.",
                    "badge": "커뮤니티",
                }
                for idx, topic in enumerate(topics, start=1)
            ]
            return user_posts + default_posts

        return []

    def show_write_community_page():
        close_overlays()
        app_state["selected_tab"] = 0
        app_state["current_page"] = "write_community"
        selected_category = app_state.get("selected_category") or "헤어"

        title_field = ft.TextField(
            width=content_width(),
            hint_text="제목을 입력해주세요.",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        content_field = ft.TextField(
            width=content_width(),
            hint_text="궁금한 점, 전후 사진 이야기, 추천 요청 등을 자유롭게 작성해보세요.",
            multiline=True,
            min_lines=6,
            max_lines=9,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )

        def go_back(e=None):
            app_state["current_page"] = "search_results"
            show_search_results_page()

        def submit_post(e):
            title = (title_field.value or "").strip()
            body_text = (content_field.value or "").strip()
            if not title:
                show_snack("글 제목을 입력해주세요.", bgcolor="#B85C5C")
                return
            if not body_text:
                show_snack("글 내용을 입력해주세요.", bgcolor="#B85C5C")
                return

            app_state.setdefault("community_posts", []).insert(0, {
                "type": "community",
                "title": f"[{selected_category}] {title}",
                "subtitle": "내 커뮤니티 게시글",
                "meta": "댓글 0 · 저장 0",
                "description": body_text,
                "badge": "커뮤니티",
                "category": selected_category,
                "created_at": datetime.now().strftime("%Y-%m-%d"),
            })
            app_state["selected_subcategory"] = "커뮤니티"
            app_state["search_results"] = build_category_browse_items(selected_category, "커뮤니티")
            app_state["category_browse_mode"] = True
            app_state["search_results_back_target"] = "category"
            show_snack("커뮤니티 글이 등록되었어요.")
            show_search_results_page()

        body = ft.Column(
            controls=[
                page_header("커뮤니티 글쓰기", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor=MAIN_COLOR_SOFT,
                                border_radius=999,
                                content=ft.Text(selected_category, size=11, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                            ),
                            ft.Text("커뮤니티에 공유할 이야기를 작성해보세요.", size=13, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("제목", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            title_field,
                            ft.Container(height=12),
                            ft.Text("내용", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            content_field,
                        ],
                        spacing=0,
                    ),
                ),
                soft_button("글 등록", MAIN_COLOR, "white", submit_post, width=content_width()),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def open_category_recommendations(main_category, sub_category):
        normalized_category = normalize_overlay_category_name(main_category)
        app_state["selected_category"] = normalized_category
        app_state["selected_subcategory"] = sub_category
        app_state["search_text"] = ""
        app_state["search_results"] = build_category_browse_items(main_category, sub_category)
        app_state["recommendation_entry"] = f"{main_category} > {sub_category}"
        app_state["category_browse_mode"] = True
        app_state["search_results_back_target"] = "category"
        app_state["left_menu_expanded"] = main_category
        app_state["selected_tab"] = 0
        app_state["current_page"] = "search_results"
        close_overlays()
        show_search_results_page()

    def overlay_bottom_spacer():
        return ft.Container(height=NAV_BAR_HEIGHT + NAV_SAFE_GAP)

    def build_left_overlay():
        return ui_build_left_overlay(
            app_state=app_state,
            app_icon=app_icon,
            close_overlays=close_overlays,
            render_current_page=render_current_page,
            open_overlay=open_overlay,
            open_category_recommendations=open_category_recommendations,
            left_overlay_categories=left_overlay_categories,
            left_overlay_icons=left_overlay_icons,
        )

    def build_right_overlay():
        return ui_build_right_overlay(
            app_icon=app_icon,
            close_overlays=close_overlays,
            render_current_page=render_current_page,
            build_my_info_profile_card=build_my_info_profile_card,
            build_my_info_menu_section=build_my_info_menu_section,
        )

    def build_my_info_profile_card(width=None):
        width = width or layout_metrics()["content_width"]
        return ft.Container(
            width=width,
            padding=SPACE_LG,
            bgcolor="#FFFDFC",
            border_radius=28,
            border=ft.border.all(1, ft.Colors.with_opacity(0.76, BORDER_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=22,
                color="#0D8B6B4F",
                offset=ft.Offset(0, 10),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=64,
                                height=64,
                                border_radius=999,
                                bgcolor="#F7F0E9",
                                border=ft.border.all(1, "#EFE4D9"),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.PERSON, size=34, color=MAIN_COLOR),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        app_state["current_user"]["nickname"] if app_state.get("current_user") else "FINDY 회원",
                                        size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
                                    ),
                                    ft.Text(
                                        f'{app_state["current_user"]["provider_label"]} 계정으로 로그인됨' if app_state.get("current_user") else "나에게 맞는 뷰티 기록을 관리해보세요.",
                                        size=10, color=SUBTEXT_COLOR,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                        ],
                        spacing=SPACE_MD,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Container(height=1, bgcolor=BORDER_COLOR),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                padding=ft.padding.symmetric(vertical=12),
                                bgcolor="#FFFAF6",
                                border_radius=18,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.6, BORDER_COLOR)),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    controls=[
                                        ft.Text("예약", size=10, color=SUBTEXT_COLOR),
                                        ft.Text(
                                            str(len([i for i in app_state.get("reservation_history", []) if i.get("status") != "예약 취소"])),
                                            size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
                                        ),
                                    ],
                                    spacing=3,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                expand=True,
                                padding=ft.padding.symmetric(vertical=12),
                                bgcolor="#FFFAF6",
                                border_radius=18,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.6, BORDER_COLOR)),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    controls=[
                                        ft.Text("저장", size=10, color=SUBTEXT_COLOR),
                                        ft.Text(
                                            str(len(app_state.get("saved_ids", set()))),
                                            size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
                                        ),
                                    ],
                                    spacing=3,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                expand=True,
                                padding=ft.padding.symmetric(vertical=12),
                                bgcolor="#FFFAF6",
                                border_radius=18,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.6, BORDER_COLOR)),
                                alignment=ft.Alignment(0, 0),
                                on_click=lambda e: show_my_reviews_page(),
                                ink=True,
                                content=ft.Column(
                                    controls=[
                                        ft.Text("리뷰", size=10, color=SUBTEXT_COLOR),
                                        ft.Text(
                                            str(len(app_state.get("written_reviews", []))),
                                            size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR,
                                        ),
                                    ],
                                    spacing=3,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                        ],
                    ),
                ],
                spacing=0,
            ),
        )

    def build_my_info_menu_row(
        label,
        icon_name,
        on_click=None,
        enabled=True,
        badge_text=None,
        width=None,
        expanded=False,
        has_children=False,
        arrow_icon_ref=None,
    ):
        row_width = width or content_width()
        icon_color = MAIN_COLOR if enabled else ft.Colors.with_opacity(0.45, MAIN_COLOR)
        text_color = TEXT_COLOR if enabled else ft.Colors.with_opacity(0.55, TEXT_COLOR)
        arrow_color = SUBTEXT_COLOR if enabled else ft.Colors.with_opacity(0.45, SUBTEXT_COLOR)
        row_bgcolor = "#FFFDFC" if enabled else "#FFFFFF"

        trailing_controls = []
        if badge_text:
            trailing_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=CHIP_BG if enabled else "#FFFCF8",
                    border_radius=10,
                    content=ft.Text(
                        badge_text,
                        size=10,
                        color=TEXT_COLOR if enabled else SUBTEXT_COLOR,
                        weight=ft.FontWeight.W_600,
                    ),
                )
            )
        arrow_icon = ft.Icon(
            app_icon(
                "KEYBOARD_ARROW_DOWN" if has_children and expanded else "CHEVRON_RIGHT",
                "EXPAND_MORE" if has_children and expanded else "ARROW_FORWARD_IOS",
                "ARROW_FORWARD",
            ),
            size=15,
            color=arrow_color,
        )
        if arrow_icon_ref is not None:
            arrow_icon_ref["control"] = arrow_icon
        trailing_controls.append(arrow_icon)

        return ft.Container(
            width=row_width,
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=18,
            bgcolor=row_bgcolor,
            border=ft.border.all(1, ft.Colors.with_opacity(0.0 if enabled else 0.5, BORDER_COLOR)),
            on_click=on_click if enabled else None,
            ink=enabled and on_click is not None,
            opacity=1.0 if enabled else 0.9,
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(app_icon(icon_name), size=18, color=icon_color),
                            ft.Text(label, size=15, color=text_color, weight=ft.FontWeight.W_500),
                        ],
                        spacing=SPACE_MD,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=trailing_controls,
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def build_my_info_child_row(label, on_click=None, enabled=True, badge_text=None, width=None):
        row_width = max(220, (width or content_width()) - 28)
        text_color = TEXT_COLOR if enabled else ft.Colors.with_opacity(0.55, TEXT_COLOR)
        trailing_controls = []
        if badge_text:
            trailing_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=7, vertical=2),
                    bgcolor=CHIP_BG,
                    border_radius=9,
                    content=ft.Text(badge_text, size=9, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                )
            )
        trailing_controls.append(
            ft.Icon(
                app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"),
                size=12,
                color=SUBTEXT_COLOR if enabled else ft.Colors.with_opacity(0.45, SUBTEXT_COLOR),
            )
        )
        return ft.Container(
            width=row_width,
            margin=ft.margin.only(left=28),
            padding=ft.padding.symmetric(horizontal=12, vertical=9),
            border_radius=16,
            bgcolor="#FFFDFC",
            border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
            on_click=on_click if enabled else None,
            ink=enabled and on_click is not None,
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=6, height=6, border_radius=999, bgcolor=MAIN_COLOR),
                            ft.Text(label, size=13, color=text_color, weight=ft.FontWeight.W_500),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(controls=trailing_controls, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def build_my_info_menu_group(title, subtitle, items, width=None):
        width = width or layout_metrics()["content_width"]
        expanded_sections = app_state.setdefault("my_info_expanded_sections", set())

        def toggle_section(label, children_container, arrow_icon_ref):
            def handler(e=None):
                if label in expanded_sections:
                    expanded_sections.remove(label)
                else:
                    expanded_sections.add(label)
                expanded = label in expanded_sections
                children_container.visible = expanded
                arrow_icon = arrow_icon_ref.get("control")
                if arrow_icon:
                    arrow_icon.name = app_icon(
                        "KEYBOARD_ARROW_DOWN" if expanded else "CHEVRON_RIGHT",
                        "EXPAND_MORE" if expanded else "ARROW_FORWARD_IOS",
                        "ARROW_FORWARD",
                    )
                    try:
                        arrow_icon.update()
                    except Exception:
                        pass
                try:
                    children_container.update()
                except Exception:
                    page.update()
            return handler

        controls = [
            ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
            ft.Container(height=6),
        ]

        for item in items:
            children = item.get("children", [])
            is_expanded = item["label"] in expanded_sections
            arrow_icon_ref = {}
            children_container = ft.Container(
                visible=bool(children) and is_expanded,
                padding=ft.padding.only(top=5, bottom=7),
                content=ft.Column(
                    controls=[
                        build_my_info_child_row(
                            child["label"],
                            child.get("action"),
                            enabled=child.get("enabled", True),
                            badge_text=child.get("badge_text"),
                            width=width,
                        )
                        for child in children
                    ],
                    spacing=6,
                ),
            )
            controls.append(
                build_my_info_menu_row(
                    item["label"],
                    item["icon_name"],
                    toggle_section(item["label"], children_container, arrow_icon_ref) if children else item.get("action"),
                    enabled=item.get("enabled", True),
                    badge_text=item.get("badge_text"),
                    width=width,
                    expanded=is_expanded,
                    has_children=bool(children),
                    arrow_icon_ref=arrow_icon_ref,
                )
            )
            if children:
                controls.append(children_container)

        return ft.Container(
            width=width,
            padding=ft.padding.only(bottom=4),
            content=ft.Column(
                controls=controls,
                spacing=2,
            ),
        )

    def show_review_page():
        app_state["current_page"] = "review"

        my_count = len(app_state.get("written_reviews", []))

        def open_treatment_review(e=None):
            app_state["review_target"] = None
            app_state["current_page"] = "write_review"
            show_write_review_page()

        my_reviews_banner = ft.GestureDetector(
            on_tap=lambda e: show_my_reviews_page(),
            content=ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                bgcolor=MAIN_COLOR_SOFT,
                border_radius=RADIUS_LG,
                border=ft.border.all(1, ft.Colors.with_opacity(0.25, MAIN_COLOR)),
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.RATE_REVIEW_OUTLINED, size=20, color=MAIN_COLOR),
                        ft.Column(
                            controls=[
                                ft.Text("내가 쓴 리뷰", size=14, weight=ft.FontWeight.W_600, color=MAIN_COLOR),
                                ft.Text(
                                    f"작성한 리뷰 {my_count}개" if my_count else "아직 작성한 리뷰가 없어요",
                                    size=11, color=ft.Colors.with_opacity(0.75, MAIN_COLOR),
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        )

        write_review_banner = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=open_treatment_review,
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD_COMMENT_OUTLINED, size=20, color=MAIN_COLOR),
                    ft.Column(
                        controls=[
                            ft.Text("시술받은 아티스트로 리뷰 작성", size=14, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Text("완료된 시술에서 아티스트를 선택해 남겨보세요.", size=11, color=SUBTEXT_COLOR),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=SUBTEXT_COLOR),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        body = ft.Column(
            controls=[
                page_header("리뷰"),
                ft.Container(height=10),
                my_reviews_banner,
                write_review_banner,
                ft.Container(height=4),
                ft.Container(
                    width=content_width(),
                    content=ft.Column(
                        controls=[
                            review_card(name, category, review)
                            for name, category, review in get_review_items()
                        ],
                        spacing=SPACE_MD,
                    ),
                ),
                ft.Container(height=20),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state.get("selected_tab", 2))

    def show_write_review_page():
        app_state["current_page"] = "write_review"
        app_state["selected_tab"] = 4
        item = app_state.get("review_target")

        selected_rating = [0]
        selected_photos = []
        selectable_items = []
        seen_reservation_ids = set()
        candidates = ([item] if item else []) + list(reversed(app_state.get("reservation_history", [])))
        for candidate in candidates:
            reservation_id = candidate.get("id")
            if reservation_id in seen_reservation_ids:
                continue
            if classify_history_item(candidate) == "past" or candidate.get("status") == "시술 완료" or candidate == item:
                selectable_items.append(candidate)
                seen_reservation_ids.add(reservation_id)
        if not selectable_items:
            show_snack("리뷰를 작성할 수 있는 완료된 시술이 없어요.", bgcolor="#B85C5C")
            show_review_page()
            return
        selected_item = [selectable_items[0]]

        star_row = ft.Row(spacing=6, alignment=ft.MainAxisAlignment.CENTER)

        def update_stars(n):
            selected_rating[0] = n
            star_row.controls.clear()
            for i in range(1, 6):
                star_row.controls.append(
                    ft.GestureDetector(
                        on_tap=lambda e, v=i: [update_stars(v), page.update()],
                        content=ft.Text(
                            "★" if i <= selected_rating[0] else "☆",
                            size=32,
                            color=MAIN_COLOR if i <= selected_rating[0] else BORDER_COLOR,
                        ),
                    )
                )
            page.update()

        update_stars(0)

        content_field = ft.TextField(
            hint_text="시술 결과, 아티스트 응대, 분위기 등을 자유롭게 남겨주세요.",
            multiline=True,
            min_lines=5,
            max_lines=8,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
            width=content_width(),
        )

        selected_artist_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
        selected_meta_text = ft.Text("", size=12, color=SUBTEXT_COLOR)
        artist_option_controls = []

        def refresh_artist_selection():
            current = selected_item[0]
            selected_artist_text.value = current.get("artist_name", "")
            selected_meta_text.value = f'{current.get("service", current.get("category", ""))}  ·  {current.get("date", "")}'
            for control, option in artist_option_controls:
                active = option.get("id") == current.get("id")
                control.bgcolor = MAIN_COLOR if active else "#FFFFFF"
                control.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
                control.content.controls[0].color = "#FFFFFF" if active else TEXT_COLOR
                control.content.controls[1].color = "#FFFFFF" if active else SUBTEXT_COLOR

        def select_artist(option):
            def handler(e):
                selected_item[0] = option
                refresh_artist_selection()
                page.update()
            return handler

        artist_option_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
        for option in selectable_items:
            option_card = ft.Container(
                width=142,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=14,
                ink=True,
                on_click=select_artist(option),
                content=ft.Column(
                    controls=[
                        ft.Text(option.get("artist_name", ""), size=12, weight=ft.FontWeight.W_600, max_lines=1),
                        ft.Text(option.get("service", option.get("category", "")), size=10, max_lines=1),
                    ],
                    spacing=3,
                ),
            )
            artist_option_controls.append((option_card, option))
            artist_option_row.controls.append(option_card)

        refresh_artist_selection()

        photo_count_text = ft.Text("0/10", size=11, color=SUBTEXT_COLOR)

        photos_row = ft.Row(controls=[], spacing=8, scroll=ft.ScrollMode.AUTO)
        photos_preview_container = ft.Container(
            width=content_width(),
            visible=False,
            margin=ft.margin.only(top=8),
            content=photos_row,
        )

        def refresh_photo_preview():
            photos_row.controls.clear()
            for idx, path in enumerate(selected_photos):
                def make_remove(i):
                    def remove_photo(e):
                        selected_photos.pop(i)
                        refresh_photo_preview()
                    return remove_photo

                photos_row.controls.append(
                    ft.Stack(
                        controls=[
                            ft.Container(
                                width=80,
                                height=80,
                                border_radius=10,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Image(src=path, width=80, height=80, fit=ft.ImageFit.COVER),
                            ),
                            ft.Container(
                                right=4,
                                top=4,
                                width=22,
                                height=22,
                                bgcolor=ft.Colors.with_opacity(0.72, "#000000"),
                                border_radius=11,
                                alignment=ft.Alignment(0, 0),
                                on_click=make_remove(idx),
                                content=ft.Icon(ft.Icons.CLOSE_ROUNDED, size=13, color="#FFFFFF"),
                            ),
                        ],
                        width=80,
                        height=80,
                    )
                )
            photos_preview_container.visible = len(selected_photos) > 0
            photo_count_text.value = f"{len(selected_photos)}/10"
            page.update()

        def on_files_picked(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            remaining = 10 - len(selected_photos)
            new_files = e.files[:remaining]
            for f in new_files:
                if f.path:
                    selected_photos.append(f.path)
            refresh_photo_preview()
            if len(e.files) > remaining:
                show_snack("사진은 최대 10장까지 선택할 수 있어요.", bgcolor="#B85C5C")

        file_picker = ft.FilePicker(on_result=on_files_picked)
        page.overlay.append(file_picker)
        page.update()

        def pick_photos(e):
            if len(selected_photos) >= 10:
                show_snack("사진은 최대 10장까지 선택할 수 있어요.", bgcolor="#B85C5C")
                return
            file_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "gif"],
            )

        def cleanup_file_picker():
            if file_picker in page.overlay:
                page.overlay.remove(file_picker)

        def submit_review(e):
            if selected_rating[0] == 0:
                show_snack("별점을 선택해주세요.", bgcolor="#B85C5C")
                return
            text = (content_field.value or "").strip()
            if not text:
                show_snack("리뷰 내용을 입력해주세요.", bgcolor="#B85C5C")
                return

            target_item = selected_item[0]
            already_written = any(
                r.get("reservation_id") == target_item.get("id")
                for r in app_state.get("written_reviews", [])
            )
            if already_written:
                show_snack("이미 이 시술 리뷰를 작성했어요.", bgcolor="#B85C5C")
                return

            review = {
                "reservation_id": target_item.get("id"),
                "artist_id": target_item.get("artist_id"),
                "artist_name": target_item.get("artist_name", ""),
                "job": target_item.get("job", ""),
                "category": target_item.get("category", target_item.get("service", "")),
                "service": target_item.get("service", target_item.get("category", "")),
                "rating": selected_rating[0],
                "content": text,
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "photos": list(selected_photos),
            }
            cleanup_file_picker()
            app_state.setdefault("written_reviews", []).append(review)
            show_snack("리뷰가 등록되었어요. 감사합니다!")
            app_state["review_target"] = None
            show_reservation_history_page()

        def go_back(e):
            cleanup_file_picker()
            app_state["review_target"] = None
            show_reservation_history_page()

        photo_add_button = ft.GestureDetector(
            on_tap=pick_photos,
            content=ft.Container(
                width=content_width(),
                height=52,
                border_radius=RADIUS_MD,
                border=ft.border.all(1.5, BORDER_COLOR),
                bgcolor="#FAFAF8",
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, size=18, color=MAIN_COLOR),
                        ft.Text("사진 추가", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        photo_count_text,
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=16),
            ),
        )

        body = ft.Column(
            controls=[
                page_header("리뷰 작성", on_back=go_back),
                ft.Container(height=12),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("시술받은 아티스트", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=4),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=42,
                                        height=42,
                                        border_radius=14,
                                        bgcolor="#000000",
                                    ),
                                    ft.Column(
                                        controls=[
                                            selected_artist_text,
                                            selected_meta_text,
                                        ],
                                        spacing=3,
                                        expand=True,
                                    ),
                                ],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(height=10),
                            artist_option_row,
                        ],
                        spacing=0,
                    ),
                ),
                ft.Container(height=8),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("별점", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=4),
                            star_row,
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=8),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("리뷰 내용", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            content_field,
                        ],
                        spacing=0,
                    ),
                ),
                ft.Container(height=8),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("사진 첨부", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Text("최대 10장까지 첨부할 수 있어요.", size=11, color=SUBTEXT_COLOR),
                            ft.Container(height=8),
                            photo_add_button,
                            photos_preview_container,
                        ],
                        spacing=4,
                    ),
                ),
                ft.Container(height=16),
                soft_button("리뷰 등록", MAIN_COLOR, "white", submit_review, width=content_width()),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_placeholder_info_page(title=None, description=None):
        if title is not None or description is not None:
            app_state["placeholder_info"] = {
                "title": title or "안내",
                "description": description or "",
            }
        placeholder = app_state.get("placeholder_info", {})
        title = placeholder.get("title", title or "안내")
        description = placeholder.get("description", description or "")
        app_state["selected_tab"] = 4
        app_state["current_page"] = "placeholder_info"

        body = ft.Column(
            controls=[
                page_header(title, on_back=go_back_page),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(description, size=13, color=SUBTEXT_COLOR),
                        ],
                        spacing=SPACE_MD,
                    ),
                ),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_cancel_reservation_dialog(item):
        if not item:
            return

        def close_dialog(e=None):
            if page.dialog:
                page.dialog.open = False
                page.update()

        def confirm_dialog(e):
            cancelled = cancel_reservation(item.get("id"))
            close_dialog()
            if cancelled:
                show_snack("예약이 취소되었어요.")
                show_reservation_history_page()

        page.dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=22),
            title=ft.Text("예약을 취소할까요?", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            content=ft.Column(
                controls=[
                    ft.Text(f'{item.get("artist_name", "")} · {item.get("service", item.get("category", "기본 시술"))}', size=13, color=TEXT_COLOR),
                    ft.Text(f'{item.get("date", "")} · {item.get("time", "")}', size=12, color=SUBTEXT_COLOR),
                    ft.Text("취소된 예약은 예약내역에 남고, 같은 시간은 다시 예약할 수 있어요.", size=12, color=SUBTEXT_COLOR),
                ],
                spacing=8,
                tight=True,
            ),
            actions_alignment=ft.MainAxisAlignment.END,
            actions=[
                ft.TextButton("닫기", on_click=close_dialog),
                ft.TextButton("예약 취소", on_click=confirm_dialog, style=ft.ButtonStyle(color="#B85C5C")),
            ],
        )
        page.dialog.open = True
        page.update()

    def classify_history_item(item):
        if item.get("status") in {"예약 취소", "노쇼"}:
            return "cancelled"
        dt = reservation_datetime(item.get("date"), item.get("time"))
        if dt and dt < datetime.now():
            return "past"
        return "upcoming"

    def history_section(title, subtitle, items, empty_text):
        cards = [reservation_history_card(item) for item in items]
        if not cards:
            cards = [
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=18),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text(empty_text, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            ]
        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FCFBF8",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                    ft.Container(height=6),
                    *cards,
                ],
                spacing=SPACE_SM,
            ),
        )

    def show_my_reviews_page():
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my_reviews"

        reviews = list(reversed(app_state.get("written_reviews", [])))

        def go_back(e):
            go_back_page(e)

        def open_treatment_review(e=None):
            app_state["review_target"] = None
            app_state["current_page"] = "write_review"
            show_write_review_page()

        write_review_button = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor=MAIN_COLOR_SOFT,
            border_radius=RADIUS_LG,
            border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
            on_click=open_treatment_review,
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD_COMMENT_OUTLINED, size=18, color=MAIN_COLOR),
                    ft.Text("시술받은 아티스트로 리뷰 작성", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        def _my_review_card(r):
            rating = r.get("rating", 5)
            photos = r.get("photos", [])
            card_controls = [
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(r.get("artist_name", ""), size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ft.Text(r.get("created_at", ""), size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=9, vertical=4),
                            bgcolor=CHIP_BG,
                            border_radius=10,
                            border=ft.border.all(1, BORDER_COLOR),
                            content=ft.Text(r.get("category", ""), size=10, color=TEXT_COLOR),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.STAR_ROUNDED, size=14,
                            color=MAIN_COLOR if i < rating else BORDER_COLOR,
                        )
                        for i in range(5)
                    ],
                    spacing=1,
                ),
                ft.Text(r.get("content", ""), size=12, color=SUBTEXT_COLOR),
            ]
            if photos:
                card_controls.append(
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=68, height=68,
                                border_radius=8,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Image(src=p, width=68, height=68, fit=ft.ImageFit.COVER),
                            )
                            for p in photos[:10]
                        ],
                        spacing=6,
                        scroll=ft.ScrollMode.AUTO,
                    )
                )
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(controls=card_controls, spacing=8),
            )

        if not reviews:
            list_content = ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=16, vertical=32),
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.RATE_REVIEW_OUTLINED, size=44, color=BORDER_COLOR),
                        ft.Text("아직 작성한 리뷰가 없어요", size=15, weight=ft.FontWeight.W_500, color=TEXT_COLOR),
                        ft.Text("시술 완료 후 예약 내역에서 리뷰를 남겨보세요.", size=12, color=SUBTEXT_COLOR),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            body_controls = [
                page_header("내가 쓴 리뷰", on_back=go_back),
                ft.Container(height=12),
                write_review_button,
                list_content,
                ft.Container(height=24),
            ]
        else:
            body_controls = [
                page_header("내가 쓴 리뷰", on_back=go_back),
                ft.Text(
                    f"총 {len(reviews)}개의 리뷰를 작성했어요.",
                    size=12, color=SUBTEXT_COLOR,
                ),
                write_review_button,
                ft.Container(height=4),
                *[_my_review_card(r) for r in reviews],
                ft.Container(height=24),
            ]

        body = ft.Column(
            controls=body_controls,
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_reservation_history_page():
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "reservation_history"

        history = list(reversed(app_state.get("reservation_history", [])))
        upcoming_items = [item for item in history if classify_history_item(item) == "upcoming"]
        past_items = [item for item in history if classify_history_item(item) == "past"]
        cancelled_items = [item for item in history if classify_history_item(item) == "cancelled"]

        controls = [
            page_header("예약내역", on_back=go_back_page),
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_XL,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        
                        ft.Text("다가오는 예약, 지난 예약, 취소된 예약을 한눈에 확인할 수 있어요.", size=13, color=SUBTEXT_COLOR),
                    ],
                    spacing=10,
                ),
            ),
            history_section("다가오는 예약", "변경이 필요하면 여기서 취소할 수 있어요.", upcoming_items, "예정된 예약이 없어요."),
            history_section("지난 예약", "방문이 끝났거나 시간이 지난 예약이에요.", past_items, "지난 예약이 아직 없어요."),
            history_section("취소된 예약", "취소된 예약도 기록으로 남겨둘게요.", cancelled_items, "취소된 예약이 없어요."),
            ft.Container(height=24),
        ]

        body = ft.Column(
            controls=controls,
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def reservation_history_card(item):
        status_color, status_label = get_reservation_status_meta(item.get("status"))
        kind = classify_history_item(item)

        def cancel_click(e):
            e.stop_propagation = True
            show_cancel_reservation_dialog(item)

        written_reviews = app_state.get("written_reviews", [])
        written_review = next((r for r in written_reviews if r["reservation_id"] == item.get("id")), None)
        already_reviewed = written_review is not None

        def review_click(e):
            e.stop_propagation = True
            app_state["review_target"] = item
            app_state["current_page"] = "write_review"
            render_current_page()

        action_controls = []
        if item.get("status") == "예약 완료" and kind == "upcoming":
            action_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor="#FFF3F0",
                    border_radius=10,
                    on_click=cancel_click,
                    ink=True,
                    content=ft.Text("예약 취소", size=12, color="#B85C5C", weight=ft.FontWeight.W_600),
                )
            )
        if kind == "past" and item.get("status") in ("예약 완료", "시술 완료"):
            if already_reviewed:
                action_controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=CHIP_BG,
                        border_radius=10,
                        content=ft.Text("리뷰 작성 완료", size=12, color=SUBTEXT_COLOR),
                    )
                )
            else:
                action_controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=MAIN_COLOR_SOFT,
                        border_radius=10,
                        on_click=review_click,
                        ink=True,
                        content=ft.Text("리뷰 작성", size=12, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                    )
                )

        meta_text = f'{item.get("date", "")}  {item.get("time", "")}'
        if kind == "past" and item.get("status") == "예약 완료":
            status_color = "#4F8A5B"
            status_label = "지난 예약"

        card_controls = [
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(item.get("artist_name", ""), size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(item.get("job", ""), size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        bgcolor=ft.Colors.with_opacity(0.10, status_color),
                        border_radius=999,
                        content=ft.Text(status_label, size=11, color=status_color, weight=ft.FontWeight.W_600),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(meta_text, size=13, color=MAIN_COLOR),
            ft.Text(f'시술: {item.get("service", item.get("category", "기본 시술"))}', size=12, color=TEXT_COLOR),
            ft.Text(f'요청사항: {item.get("note", "") or "없음"}', size=12, color=SUBTEXT_COLOR),
            ft.Row(controls=action_controls, spacing=8) if action_controls else ft.Container(),
        ]

        if already_reviewed and written_review:
            review_rating = written_review.get("rating", 5)
            review_photos = written_review.get("photos", [])
            review_section_controls = [
                ft.Container(height=1, bgcolor=BORDER_COLOR),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.STAR_ROUNDED, size=13, color=MAIN_COLOR if i < review_rating else BORDER_COLOR)
                        for i in range(5)
                    ],
                    spacing=1,
                ),
                ft.Text(written_review.get("content", ""), size=12, color=SUBTEXT_COLOR),
            ]
            if review_photos:
                review_section_controls.append(
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=60,
                                height=60,
                                border_radius=8,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Image(src=p, width=60, height=60, fit=ft.ImageFit.COVER),
                            )
                            for p in review_photos[:10]
                        ],
                        spacing=6,
                        scroll=ft.ScrollMode.AUTO,
                    )
                )
            card_controls.extend(review_section_controls)

        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(controls=card_controls, spacing=8),
        )

    def build_my_info_menu_section(width=None):
        width = width or layout_metrics()["content_width"]

        beauty_items = [
            {
                "label": "나의 뷰티 정보",
                "icon_name": "SPA_OUTLINED",
                "action": lambda e: (close_overlays(), show_beauty_profile_page()),
                "enabled": True,
            },
            {
                "label": "예약내역",
                "icon_name": "CALENDAR_MONTH",
                "action": lambda e: (close_overlays(), show_reservation_history_page()),
                "enabled": True,
            },
            {
                "label": "완료한 시술",
                "icon_name": "CHECK_CIRCLE_OUTLINE",
                "action": lambda e: (close_overlays(), show_completed_page()),
                "enabled": True,
            },
            {
                "label": "취소된 시술",
                "icon_name": "EVENT_BUSY",
                "action": lambda e: (close_overlays(), show_cancelled_treatments_page()),
                "enabled": True,
                "badge_text": "취소 · 노쇼",
            },
        ]

        activity_items = [
            {
                "label": "내가 쓴 글",
                "icon_name": "ARTICLE_OUTLINED",
                "action": lambda e: (close_overlays(), show_my_reviews_page()),
                "enabled": True,
                "children": [
                    {"label": "리뷰", "action": lambda e: (close_overlays(), show_my_reviews_page())},
                    {"label": "스냅", "action": lambda e: (close_overlays(), show_placeholder_info_page("내가 쓴 스냅", "작성한 스냅을 모아볼 수 있게 준비 중이에요."))},
                    {"label": "비디오", "action": lambda e: (close_overlays(), show_placeholder_info_page("내가 쓴 비디오", "업로드한 영상을 모아볼 수 있게 준비 중이에요."))},
                    {"label": "커뮤니티", "action": lambda e: (close_overlays(), show_placeholder_info_page("내가 쓴 커뮤니티", "작성한 커뮤니티 글을 모아볼 수 있게 준비 중이에요."))},
                ],
            },
            {
                "label": "저장한 뷰티",
                "icon_name": "BOOKMARK_BORDER",
                "action": lambda e: (close_overlays(), show_saved_page()),
                "enabled": True,
                "children": [
                    {"label": "샵", "action": lambda e: (close_overlays(), show_placeholder_info_page("저장한 샵", "저장한 샵을 모아볼 수 있게 준비 중이에요."))},
                    {"label": "아티스트", "action": lambda e: (close_overlays(), show_saved_page())},
                    {"label": "스냅", "action": lambda e: (close_overlays(), show_placeholder_info_page("저장한 스냅", "저장한 스냅을 모아볼 수 있게 준비 중이에요."))},
                    {"label": "비디오", "action": lambda e: (close_overlays(), show_placeholder_info_page("저장한 비디오", "저장한 영상을 모아볼 수 있게 준비 중이에요."))},
                ],
            },
        ]

        support_items = [
            {
                "label": "공지사항",
                "icon_name": "CAMPAIGN",
                "action": lambda e: (close_overlays(), show_notice_page()),
                "enabled": True,
            },
            {
                "label": "개선 의견",
                "icon_name": "LIGHTBULB_OUTLINE",
                "action": lambda e: (close_overlays(), show_feedback_page()),
                "enabled": True,
            },
            {
                "label": "고객센터",
                "icon_name": "SUPPORT_AGENT",
                "action": lambda e: (close_overlays(), show_support_page()),
                "enabled": True,
                "children": [
                    {"label": "1:1문의", "action": lambda e: (close_overlays(), show_support_page())},
                    {
                        "label": "1:1문의 내역",
                        "action": lambda e: (close_overlays(), show_inquiry_page()),
                        "badge_text": f'{len(app_state.get("inquiry_history", []))}건' if app_state.get("inquiry_history") else None,
                    },
                ],
            },
        ]

        def divider():
            return ft.Container(
                width=width,
                margin=ft.margin.symmetric(vertical=8),
                border=ft.border.only(top=ft.BorderSide(1, BORDER_COLOR)),
            )

        controls = [
            build_my_info_menu_group(
                "뷰티 관리",
                "예약과 시술 기록을 확인해보세요.",
                beauty_items,
                width=width,
            ),
            divider(),
            build_my_info_menu_group(
                "내 활동",
                "작성한 콘텐츠와 저장한 뷰티를 모아볼 수 있어요.",
                activity_items,
                width=width,
            ),
            divider(),
            build_my_info_menu_group(
                "고객 지원",
                "공지, 의견, 문의를 확인하고 남길 수 있어요.",
                support_items,
                width=width,
            ),
        ]

        return ft.Container(
            width=width,
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=14,
                color="#13000000",
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                controls=controls,
                spacing=0,
            ),
        )

    def nav_bar(selected_index):

        def nav_item(icon_name, active_icon_name, label, index, on_click):
            icon_color = SUBTEXT_COLOR
            text_color = SUBTEXT_COLOR
            bg_color = ft.Colors.TRANSPARENT
            icon_value = app_icon(icon_name)

            return ft.Container(
                expand=True,
                height=40,
                border_radius=14,
                bgcolor=bg_color,
                ink=True,
                on_click=on_click,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    controls=[
                        ft.Icon(icon_value, size=15, color=icon_color),
                        ft.Text(label, size=9, color=text_color, weight=ft.FontWeight.W_600),
                    ],
                    spacing=1,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        return ft.Container(
            height=62,
            margin=ft.margin.only(left=0, right=0, bottom=0, top=0),
            padding=ft.padding.only(left=8, right=8, top=4, bottom=6),
            bgcolor=ft.Colors.with_opacity(0.98, "#FFFCFA"),
            border_radius=ft.border_radius.only(top_left=22, top_right=22, bottom_left=0, bottom_right=0),
            border=ft.border.only(top=ft.BorderSide(0.8, ft.Colors.with_opacity(0.24, BORDER_COLOR))),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color="#12000000",
                offset=ft.Offset(0, -1),
            ),
            content=ft.Row(
                controls=[
                    nav_item("MENU", "MENU", "카테고리", 0, open_left_menu),
                    nav_item("PHOTO_LIBRARY_OUTLINED", "PHOTO_LIBRARY", "스냅", 1, go_snap_page),
                    nav_item("HOME_OUTLINED", "HOME", "홈", 2, go_home_page),
                    nav_item("SMART_DISPLAY_OUTLINED", "SMART_DISPLAY", "비디오", 3, go_video_page),
                    nav_item("PERSON_OUTLINE", "PERSON", "내정보", 4, open_right_menu),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    def render_phone_frame(body_content, nav_index=None):
        current_page = app_state.get("current_page", "home")
        last_page = app_state.get("_last_rendered_page")
        page_changed = current_page != last_page
        if page_changed:
            if last_page and last_page != current_page and not (last_page == "login" and current_page == "home"):
                history = app_state.setdefault("page_history", [])
                if not history or history[-1] != last_page:
                    history.append(last_page)
            app_state["_last_rendered_page"] = current_page
        preserve_scroll_pages = {"reservation", "reservation_confirm", "reservation_complete", "my"}
        full_height_pages = {"login"}
        nav_safe_bottom = (NAV_BAR_HEIGHT + NAV_SAFE_GAP) if nav_index is not None else 12
        nav_spacer = ft.Container(height=nav_safe_bottom)

        if current_page in preserve_scroll_pages:
            scroll_offset_key = "my_scroll_offset" if current_page == "my" else "reservation_scroll_offset"

            def remember_scroll(e):
                try:
                    app_state[scroll_offset_key] = e.pixels
                except Exception:
                    pass

            scroll_view = ft.ListView(
                expand=True,
                spacing=0,
                padding=0,
                auto_scroll=False,
                on_scroll=remember_scroll,
                controls=[body_content, nav_spacer],
            )

            body_wrapper = ft.Container(
                expand=True,
                padding=ft.padding.only(top=16, bottom=8),
                content=scroll_view,
            )
        elif current_page in full_height_pages:
            scroll_view = None
            body_wrapper = ft.Container(
                expand=True,
                padding=0,
                content=body_content,
            )
        else:
            scroll_view = None
            body_wrapper = ft.Container(
                expand=True,
                padding=ft.padding.only(top=16, bottom=8),
                content=ft.Column(
                    controls=[body_content, nav_spacer],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            )

        should_animate_page = page_changed and current_page not in {"login", "home_category_transition"}
        if should_animate_page:
            body_wrapper.opacity = 0
            body_wrapper.offset = ft.Offset(0, 0.025)
            body_wrapper.animate_opacity = ft.Animation(170, ft.AnimationCurve.EASE_OUT)
            body_wrapper.animate_offset = ft.Animation(170, ft.AnimationCurve.EASE_OUT)

        phone_frame = ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            bgcolor=BG_COLOR,
            border_radius=34,
            clip_behavior=ft.ClipBehavior.NONE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#14000000",
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                controls=[body_wrapper],
                spacing=0,
                expand=True,
            ),
        )

        stack_controls = [phone_frame]
        if nav_index is not None:
            stack_controls.append(
                ft.Container(
                    width=full_phone_width(),
                    height=NAV_BAR_HEIGHT,
                    bottom=0,
                    left=0,
                    right=0,
                    margin=0,
                    padding=0,
                    alignment=ft.Alignment(0, 1),
                    content=nav_bar(nav_index),
                )
            )

        next_view = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=ft.Stack(
                width=full_phone_width(),
                height=PHONE_HEIGHT,
                controls=stack_controls,
            ),
        )

        if app_state.get("_root_mount") is None:
            app_state["_root_mount"] = next_view
            page.clean()
            page.add(app_state["_root_mount"])
        else:
            app_state["_root_mount"].content = next_view.content
        page.update()

        if should_animate_page:
            async def animate_page_enter():
                await asyncio.sleep(0.01)
                try:
                    body_wrapper.opacity = 1
                    body_wrapper.offset = ft.Offset(0, 0)
                    body_wrapper.update()
                except Exception:
                    page.update()

            page.run_task(animate_page_enter)

        if current_page in preserve_scroll_pages and scroll_view is not None:
            async def restore_scroll_position():
                await asyncio.sleep(0.01)
                try:
                    await scroll_view.scroll_to(
                        offset=app_state.get(scroll_offset_key, 0),
                        duration=0,
                    )
                except Exception:
                    try:
                        await scroll_view.scroll_to(
                            offset=app_state.get(scroll_offset_key, 0),
                        )
                    except Exception:
                        pass

            page.run_task(restore_scroll_position)

    def make_shell(content, selected_index):
        render_phone_frame(content, selected_index)

    def category_square(icon_name, label, on_click, expand=True):
        return ft.Container(
            expand=expand,
            height=98,
            bgcolor="#FFFFFF",
            border_radius=20,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=on_click,
            ink=True,
            content=ft.Column(
                controls=[
                    ft.Icon(app_icon(icon_name), size=22, color=MAIN_COLOR),
                    ft.Text(
                        label,
                        size=10,
                        weight=ft.FontWeight.W_600,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=7,
            ),
        )

    def feature_card(title, desc, emoji):
        return ft.Container(
            width=half_card_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#10000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=148,
                        height=118,
                        bgcolor="#FFFCF8",
                        border_radius=RADIUS_MD,
                        content=ft.Column(
                            controls=[
                                ft.Text(emoji, size=34),
                                ft.Text(
                                    title,
                                    size=12,
                                    color=SUBTEXT_COLOR,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    ),
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text(desc, size=12, color=SUBTEXT_COLOR),
                ],
                spacing=2,
            ),
        )

    def get_snap_items():
        return list(SNAP_ITEMS)

    def snap_feature_card(title, desc, emoji, focused=False):
        card_width = 132
        image_width = 132
        image_height = 132
        emoji_size = 32
        title_size = 13
        desc_size = 10

        return ft.Container(
            width=card_width,
            padding=6,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color="#0D000000",
                offset=ft.Offset(0, 5),
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=image_width,
                        height=image_height,
                        border_radius=RADIUS_MD,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        bgcolor="#000000",
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    expand=True,
                                    bgcolor="#000000",
                                ),
                                ft.Container(
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(emoji, size=emoji_size, color="#FFFFFF"),
                                ),
                                ft.Container(
                                    left=8,
                                    top=8,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    bgcolor=ft.Colors.with_opacity(0.78, "#FFFFFF"),
                                    border_radius=999,
                                    content=ft.Text("SNAP", size=8, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                                ),
                            ]
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.only(left=2, right=2, top=4, bottom=2),
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    title,
                                    size=title_size,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_COLOR,
                                    max_lines=1,
                                ),
                                ft.Text(
                                    desc,
                                    size=desc_size,
                                    color=SUBTEXT_COLOR,
                                    max_lines=2,
                                ),
                            ],
                            spacing=3,
                        ),
                    ),
                ],
                spacing=6,
            ),
        )

    def build_snap_carousel():
        snap_items = get_snap_items()
        current_width = content_width()

        cards_row = ft.Row(
            controls=[
                snap_feature_card(title, desc, emoji, focused=(idx == 1))
                for idx, (title, desc, emoji) in enumerate(snap_items)
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            width=content_width(),
            height=214,
            clip_behavior=ft.ClipBehavior.NONE,
            content=cards_row,
        )

    def get_review_items():
        return list(REVIEW_ITEMS)

    def build_review_carousel():
        review_items = get_review_items()
        current_width = content_width()

        review_cards = ft.Column(
            controls=[
                review_card(name, category, review)
                for name, category, review in review_items
            ],
            spacing=SPACE_MD,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            width=content_width(),
            height=392,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=review_cards,
        )

    def free_request_field(initial_value=""):
        return ft.TextField(
            width=field_width(),
            value=initial_value,
            multiline=True,
            min_lines=6,
            max_lines=8,
            border_radius=4,
            bgcolor=CARD_COLOR,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=SPACE_LG,
            hint_text=(
                "예시:\n"
                "사는곳: 성수동\n"
                "성별: 여성\n"
                "나이: 24\n"
                "원하는 스타일: 청순하고 세련된 느낌\n"
                "디자이너의 성격: 꼼꼼하고 친절한 스타일\n"
                "기타: 자연스러운 분위기, 사진 잘 나오는 스타일 원함"
            ),
            hint_style=ft.TextStyle(color="#B6ADA3", size=12),
            text_size=14,
            color=TEXT_COLOR,
        )

    

    def subcategory_request_field(selected_main, selected_sub, initial_value=""):
        hint_map = {
            "커트": "얼굴형, 길이, 원하는 느낌을 적어주세요",
            "컬러": "원하는 색상, 현재 모발 상태를 적어주세요",
            "펌": "원하는 펌 스타일과 길이를 적어주세요",
            "젤네일": "원하는 디자인이나 컬러를 적어주세요",
            "프로필/증명사진": "촬영 목적과 원하는 분위기를 적어주세요",
        }

        hint = hint_map.get(selected_sub, "원하는 스타일과 요청사항을 자유롭게 적어주세요")

        return ft.TextField(
            width=field_width(),
            value=initial_value,
            multiline=True,
            min_lines=6,
            max_lines=8,
            border_radius=4,
            bgcolor=CARD_COLOR,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=SPACE_LG,
            hint_text=hint,
            text_size=14,
            color=TEXT_COLOR,
        )

    def build_recommended_artists(user_data):
        free_text = (user_data.get("free_request") or "").lower()
        category = user_data.get("category", "")

        filtered = [a.copy() for a in base_artists if a["category"] == category] or [
            a.copy() for a in base_artists
        ]
        boosted = []

        def add_boosted(artist_id, reason_text):
            artist = find_artist_by_id(artist_id)
            if artist:
                copied = artist.copy()
                copied["reason"] = reason_text
                boosted.append(copied)

        if any(word in free_text for word in ["청순", "자연", "내추럴", "여리", "맑"]):
            add_boosted("a1", "입력한 요청에서 자연스럽고 맑은 분위기가 강하게 보여 우선 추천해요.")
        if any(word in free_text for word in ["세련", "도시", "깔끔", "고급", "정돈"]):
            add_boosted("a2", "세련되고 정돈된 느낌을 원한다는 요청과 잘 맞아요.")
        if any(word in free_text for word in ["힙", "스트릿", "개성", "유니크", "강한"]):
            add_boosted("a8", "또렷하고 개성 있는 무드를 원할 때 잘 맞는 타입이에요.")
        if any(word in free_text for word in ["친절", "꼼꼼", "세심", "상담"]):
            add_boosted("a6", "디자이너 성격을 중요하게 적어줘서 꼼꼼한 타입을 먼저 보여드려요.")
        if any(word in free_text for word in ["웨딩", "본식", "드레스"]):
            add_boosted("a5", "웨딩 분위기와 잘 맞는 스타일리스트를 우선 추천해요.")
        if any(word in free_text for word in ["사진", "촬영", "스냅"]):
            add_boosted("a7", "촬영 결과 분위기를 중요하게 적어줘서 감성 스냅 작가를 먼저 보여드려요.")

        result = []
        seen = set()
        for item in boosted + filtered:
            if item["id"] not in seen:
                result.append(item)
                seen.add(item["id"])
        return result[:8]

    def open_detail(artist, back_target="home"):
        app_state["detail_artist"] = artist
        app_state["detail_back_target"] = back_target
        show_detail_page()

    def artist_result_card(artist, back_target="search"):
        saved = is_saved(artist["id"])

        def open_card(e):
            open_detail(artist, back_target=back_target)

        def save_click(e):
            e.stop_propagation = True
            toggle_saved(artist["id"])
            if back_target == "saved":
                show_saved_page()
            elif back_target == "home":
                show_home_page()
            else:
                show_search_results_page()

        return ft.Container(
            width=content_width(),
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            padding=SPACE_LG,
            on_click=open_card,
            ink=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#12000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=92,
                                height=92,
                                border_radius=12,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=black_image_box(92, 92),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(artist["name"], size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ft.Text(artist["job"], size=12, color=SUBTEXT_COLOR),
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"⭐ {artist['rating']}", size=12, color=TEXT_COLOR),
                                            ft.Text(f"· {artist['distance']}", size=12, color=SUBTEXT_COLOR),
                                            ft.Text(f"· {artist['price']}", size=12, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=4,
                                    ),
                                    ft.Text(
                                        artist["style"],
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT_COLOR,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                        ],
                        spacing=SPACE_MD,
                    ),
                    ft.Text(artist["reason"], size=13, color=SUBTEXT_COLOR),
                    ft.Row(
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=1),
                                bgcolor=CHIP_BG,
                                border_radius=4,
                                content=ft.Text(f"#{artist['tags'][0]}", size=10, color=TEXT_COLOR),
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=1),
                                bgcolor=CHIP_BG,
                                border_radius=4,
                                content=ft.Text(f"#{artist['tags'][1]}", size=10, color=TEXT_COLOR),
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=1),
                                bgcolor=CHIP_BG,
                                border_radius=4,
                                content=ft.Text(f"#{artist['tags'][2]}", size=10, color=TEXT_COLOR),
                            ),
                        ],
                        spacing=2,
                        wrap=True,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                on_click=save_click,
                                ink=True,
                                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                bgcolor=CHIP_BG,
                                border_radius=4,
                                content=ft.Text("저장됨" if saved else "저장", size=12, color=TEXT_COLOR),
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                bgcolor=MAIN_COLOR,
                                border_radius=4,
                                content=ft.Text("상세보기", size=12, color="white"),
                            ),
                        ],
                        spacing=SPACE_MD,
                    ),
                ],
                spacing=SPACE_MD,
            ),
        )

    def compact_saved_card(artist):
        def open_card(e):
            open_detail(artist, back_target="saved")

        def remove_saved(e):
            toggle_saved(artist["id"])
            show_saved_page()

        return ft.Container(
            width=content_width(),
            padding=SPACE_MD,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=open_card,
            ink=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#11000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=70,
                        height=70,
                        border_radius=RADIUS_MD,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=black_image_box(70, 70),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(artist["name"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(artist["job"], size=12, color=SUBTEXT_COLOR),
                            ft.Text(
                                f"⭐ {artist['rating']} · {artist['distance']} · {artist['price']}",
                                size=12,
                                color=SUBTEXT_COLOR,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=app_icon("BOOKMARK", "FAVORITE"),
                        icon_color=MAIN_COLOR,
                        on_click=remove_saved,
                    ),
                ],
                spacing=SPACE_MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def home_artist_card(artist):
        def open_card(e):
            open_detail(artist, back_target="home")

        return ft.Container(
            width=half_card_width(),
            padding=SPACE_MD,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=open_card,
            ink=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#10000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=132,
                        height=96,
                        border_radius=RADIUS_MD,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=black_image_box(132, 96),
                    ),
                    ft.Text(artist["name"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text(artist["job"], size=12, color=SUBTEXT_COLOR),
                    ft.Text(f"⭐ {artist['rating']} · {artist['distance']}", size=10, color=SUBTEXT_COLOR),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=1),
                        bgcolor=CHIP_BG,
                        border_radius=4,
                        content=ft.Text(artist["tags"][0], size=10, color=TEXT_COLOR),
                    ),
                ],
                spacing=2,
            ),
        )

    def build_category_box(on_click_factory):
        slim_gap = 4
        return ft.Container(
            width=content_width(),
            padding=8,
            bgcolor=ft.Colors.with_opacity(0.55, "#FFFFFF"),
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#0E000000",
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            category_square("CUT", "헤어", on_click_factory("헤어")),
                            category_square("BRUSH", "네일아트", on_click_factory("네일아트")),
                            category_square("FACE", "메이크업", on_click_factory("메이크업")),
                        ],
                        spacing=slim_gap,
                    ),
                    ft.Row(
                        controls=[
                            category_square("AUTO_FIX_HIGH", "반영구시술", on_click_factory("반영구시술")),
                            category_square("FAVORITE", "웨딩", on_click_factory("웨딩")),
                            category_square("CAMERA_ALT", "포토", on_click_factory("포토")),
                        ],
                        spacing=slim_gap,
                    ),
                ],
                spacing=slim_gap,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def on_nav_change(e):
        app_state["selected_tab"] = e.control.selected_index
        if e.control.selected_index == 0:
            show_home_page()
        elif e.control.selected_index == 1:
            show_search_page()
        elif e.control.selected_index == 2:
            show_saved_page()
        else:
            show_my_page()

    def render_opening_frame(opening_content):
        phone_frame = ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            bgcolor=BG_COLOR,
            border_radius=34,
            clip_behavior=ft.ClipBehavior.NONE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#14000000",
                offset=ft.Offset(0, 8),
            ),
            content=opening_content,
        )

        page.clean()
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=phone_frame,
            )
        )
        page.update()

    def show_opening_page():
        opening_image = opening_visual()

        image_holder = ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            alignment=ft.Alignment(0, 0),
            content=opening_image,
            scale=1.04,
            animate_scale=ft.Animation(900, ft.AnimationCurve.EASE_OUT),
        )

        opening_overlay = ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            bgcolor=ft.Colors.with_opacity(0.10, "#FFFFFF"),
            opacity=1.0,
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT),
        )

        opening_body = ft.Stack(
            controls=[
                ft.Container(
                    width=full_phone_width(),
                    height=PHONE_HEIGHT,
                    bgcolor="#FFFFFF",
                ),
                image_holder,
                opening_overlay,
            ]
        )

        render_opening_frame(opening_body)
        if hasattr(opening_image, "opacity"):
            opening_image.opacity = 1
        image_holder.scale = 1.0
        opening_overlay.opacity = 0.0
        page.update()

    async def start_opening_flow():
        show_opening_page()
        await asyncio.sleep(OPENING_DURATION)
        show_login_page()

    def show_login_page():
        app_state["current_page"] = "login"

        async def _go_to_home_transition():
            close_overlays()
            app_state["selected_tab"] = 2
            login_card.opacity = 0
            login_card.offset = ft.Offset(0, 0.04)
            body.opacity = 0
            page.update()
            await asyncio.sleep(0.24)
            show_home_page()

        provider_user_map = {
            "네이버": ("네이버 회원", "naver"),
            "카카오": ("카카오 회원", "kakao"),
            "구글": ("Google 회원", "google"),
            "애플": ("Apple 회원", "apple"),
        }

        def go_to_home(provider):
            def handler(e):
                nickname, provider_key = provider_user_map.get(provider, (f"{provider} 회원", provider))
                app_state["current_user"] = {
                    "provider": provider_key,
                    "provider_label": provider,
                    "nickname": nickname,
                }
                show_snack(f"{provider}로 로그인하고 있어요.")
                page.run_task(_go_to_home_transition)
            return handler

        def themed_login_button(label, bgcolor, text_color, on_click, *, border=None, width=288, delay_ms=0):
            button = ft.Container(
                width=width,
                height=54,
                bgcolor=bgcolor,
                border_radius=18,
                border=border or ft.border.all(1, BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color="#0B000000",
                    offset=ft.Offset(0, 3),
                ),
                content=ft.Text(
                    label,
                    color=text_color,
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                opacity=0,
                offset=ft.Offset(0, 0.04),
                animate_opacity=ft.Animation(260, ft.AnimationCurve.EASE_OUT),
                animate_offset=ft.Animation(260, ft.AnimationCurve.EASE_OUT),
                ink=True,
                on_click=on_click,
            )

            async def reveal():
                await asyncio.sleep(delay_ms / 1000)
                button.opacity = 1
                button.offset = ft.Offset(0, 0)
                page.update()

            page.run_task(reveal)
            return button

        logo_box = ft.Container(
            padding=ft.padding.only(top=6, bottom=10),
            content=login_logo_visual(),
            opacity=0,
            offset=ft.Offset(0, -0.03),
            animate_opacity=ft.Animation(380, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(380, ft.AnimationCurve.EASE_OUT),
        )

        intro_copy = ft.Container(
            opacity=0,
            offset=ft.Offset(0, 0.03),
            animate_opacity=ft.Animation(360, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(360, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                controls=[
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        login_card = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=24, vertical=28),
            bgcolor="#FFFFFF",
            border_radius=32,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#0E000000",
                offset=ft.Offset(0, 6),
            ),
            opacity=0,
            offset=ft.Offset(0, 0.05),
            animate_opacity=ft.Animation(420, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(420, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                controls=[
                    logo_box,
                    intro_copy,
                    ft.Container(height=6),
                    themed_login_button("네이버 로그인", "#FFFFFF", TEXT_COLOR, go_to_home("네이버"), border=ft.border.all(1, BORDER_COLOR), width=288, delay_ms=140),
                    themed_login_button("카카오 로그인", "#FFFFFF", TEXT_COLOR, go_to_home("카카오"), border=ft.border.all(1, BORDER_COLOR), width=288, delay_ms=220),
                    themed_login_button("구글 로그인", "#FFFFFF", TEXT_COLOR, go_to_home("구글"), border=ft.border.all(1, BORDER_COLOR), width=288, delay_ms=300),
                    themed_login_button("애플 로그인", "#FFFFFF", TEXT_COLOR, go_to_home("애플"), border=ft.border.all(1, BORDER_COLOR), width=288, delay_ms=380),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        body = ft.Container(
            expand=True,
            bgcolor="#FFFFFF",
            alignment=ft.Alignment(0, 0),
            opacity=1,
            animate_opacity=ft.Animation(260, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Column(
                controls=[
                    ft.Container(height=24),
                    login_card,
                    ft.Container(height=24),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )

        render_phone_frame(body, None)

        async def reveal_login():
            await asyncio.sleep(0.02)
            login_card.opacity = 1
            login_card.offset = ft.Offset(0, 0)
            logo_box.opacity = 1
            logo_box.offset = ft.Offset(0, 0)
            intro_copy.opacity = 1
            intro_copy.offset = ft.Offset(0, 0)
            page.update()

        page.run_task(reveal_login)

        async def animate_login_intro():
            await asyncio.sleep(0.05)
            login_card.opacity = 1
            login_card.offset = ft.Offset(0, 0)
            logo_box.opacity = 1
            logo_box.offset = ft.Offset(0, 0)
            page.update()

        page.run_task(animate_login_intro)

    def upcoming_reservations(limit=None):
        items = [item for item in app_state.get("reservation_history", []) if classify_history_item(item) == "upcoming" and item.get("status") == "예약 완료"]
        items.sort(key=lambda item: reservation_datetime(item.get("date"), item.get("time")) or datetime.max)
        if limit is not None:
            return items[:limit]
        return items

    def reservation_notification_items():
        notices = []
        upcoming_items = upcoming_reservations()
        now_dt = datetime.now()

        for item in upcoming_items:
            dt = reservation_datetime(item.get("date"), item.get("time"))
            if not dt:
                continue
            delta = dt - now_dt
            total_seconds = int(delta.total_seconds())
            if total_seconds < 0:
                continue
            hours_left = total_seconds // 3600
            days_left = delta.days
            if dt.date() == now_dt.date():
                title = "오늘 예약이 있어요"
                body = f"{item.get('artist_name', '')} · {item.get('time', '')}"
            elif dt.date() == (now_dt.date() + timedelta(days=1)):
                title = "내일 예약이 예정되어 있어요"
                body = f"{item.get('artist_name', '')} · {item.get('date', '')} {item.get('time', '')}"
            else:
                title = f"다가오는 예약 D-{days_left}"
                body = f"{item.get('artist_name', '')} · {item.get('date', '')} {item.get('time', '')}"
            notices.append({
                "id": f"upcoming:{item.get('id')}",
                "kind": "upcoming",
                "title": title,
                "body": body,
                "timestamp": dt,
                "item": item,
            })

        for item in app_state.get("reservation_history", []):
            if item.get("status") == "예약 취소":
                dt = reservation_datetime(item.get("date"), item.get("time")) or now_dt
                notices.append({
                    "id": f"cancelled:{item.get('id')}",
                    "kind": "cancelled",
                    "title": "예약이 취소되었어요",
                    "body": f"{item.get('artist_name', '')} · {item.get('date', '')} {item.get('time', '')}",
                    "timestamp": dt,
                    "item": item,
                })

        last_completed = app_state.get("last_completed_reservation")
        if last_completed and last_completed.get("status") == "예약 완료":
            dt = reservation_datetime(last_completed.get("date"), last_completed.get("time")) or now_dt
            notices.append({
                "id": f"confirmed:{last_completed.get('id')}",
                "kind": "confirmed",
                "title": "예약이 완료되었어요",
                "body": f"{last_completed.get('artist_name', '')} · {last_completed.get('date', '')} {last_completed.get('time', '')}",
                "timestamp": dt,
                "item": last_completed,
            })

        written_ids = {r["reservation_id"] for r in app_state.get("written_reviews", [])}
        for item in app_state.get("reservation_history", []):
            if item.get("status") in ("예약 완료", "시술 완료") and item.get("id") not in written_ids:
                dt = reservation_datetime(item.get("date"), item.get("time")) or now_dt
                if dt < now_dt:
                    notices.append({
                        "id": f"review_request:{item.get('id')}",
                        "kind": "review_request",
                        "title": "리뷰를 남겨주세요",
                        "body": f"{item.get('artist_name', '')} · {item.get('date', '')} 방문 리뷰",
                        "timestamp": dt,
                        "item": item,
                    })

        unique = {}
        for notice in notices:
            unique[notice["id"]] = notice
        result = sorted(unique.values(), key=lambda x: x["timestamp"], reverse=True)
        return result

    def unread_notification_count():
        items = reservation_notification_items()
        read_at = app_state.get("notification_read_at")
        if not read_at:
            return len(items)
        return sum(1 for item in items if item["timestamp"] > read_at)

    def open_notifications_page(e=None):
        close_overlays()
        app_state["notification_read_at"] = datetime.now()
        app_state["selected_tab"] = 2
        app_state["current_page"] = "notifications"
        show_notification_page()

    def upcoming_reservation_floating_card(item):
        dt = reservation_datetime(item.get("date"), item.get("time"))
        badge_text = "다가오는 예약"
        countdown_text = build_reservation_countdown_text(item.get("date"), item.get("time"))
        schedule_text = format_reservation_date_text(item.get("date"), item.get("time"))
        if countdown_text:
            badge_text = countdown_text if countdown_text in {"내일", "지난 예약"} else f"다가오는 예약 · {countdown_text}"
            if dt and dt.date() == datetime.now().date():
                badge_text = "오늘 예약"

        def open_history(e=None):
            app_state["dismissed_upcoming_notice_id"] = item.get("id")
            show_reservation_history_page()

        def close_card(e=None):
            app_state["dismissed_upcoming_notice_id"] = item.get("id")
            show_home_page()

        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=24,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#14000000",
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor="#F7EFE6",
                                border_radius=999,
                                content=ft.Text(badge_text, size=10, weight=ft.FontWeight.BOLD, color=MAIN_COLOR),
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=app_icon("CLOSE", "CLEAR"),
                                icon_size=18,
                                icon_color=SUBTEXT_COLOR,
                                on_click=close_card,
                                tooltip="닫기",
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text("예약 일정이 있어요", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text(
                        f"{item.get('artist_name', '')} · {item.get('service', item.get('category', ''))}",
                        size=14,
                        color=TEXT_COLOR,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Text(
                        item.get('job', ''),
                        size=12,
                        color=SUBTEXT_COLOR,
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CALENDAR_MONTH, size=15, color=MAIN_COLOR),
                            ft.Text(schedule_text, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SCHEDULE, size=15, color=MAIN_COLOR),
                            ft.Text(
                                countdown_text or item.get("status", "예약 완료"),
                                size=12,
                                color=SUBTEXT_COLOR,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                                bgcolor=MAIN_COLOR,
                                border_radius=14,
                                on_click=open_history,
                                ink=True,
                                content=ft.Text("예약내역 보기", size=12, color="white", weight=ft.FontWeight.W_600),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=0,
            ),
        )

    def notification_card(item):
        kind = item.get("kind")
        accent = MAIN_COLOR if kind in {"upcoming", "confirmed", "review_request"} else "#B85C5C"
        bg = "#FFFFFF" if kind != "cancelled" else "#FFF7F5"
        if kind == "upcoming":
            icon_name = "NOTIFICATIONS_ACTIVE"
        elif kind == "confirmed":
            icon_name = "CHECK_CIRCLE"
        elif kind == "review_request":
            icon_name = "RATE_REVIEW"
        else:
            icon_name = "EVENT_BUSY"

        def open_notice_target(e=None):
            if kind == "review_request" and item.get("item"):
                app_state["review_target"] = item["item"]
                app_state["current_page"] = "write_review"
                render_current_page()
            elif item.get("item"):
                show_reservation_history_page()

        timestamp_label = item.get("timestamp").strftime("%m.%d %H:%M") if item.get("timestamp") else ""

        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor=bg,
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=open_notice_target,
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=999,
                        bgcolor="#F7EFE6" if kind != "cancelled" else "#FBE7E3",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(app_icon(icon_name, "NOTIFICATIONS"), size=18, color=accent),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(item.get("title", ""), size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(item.get("body", ""), size=12, color=SUBTEXT_COLOR),
                            ft.Text(timestamp_label, size=10, color=SUBTEXT_COLOR),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"), size=15, color=SUBTEXT_COLOR),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )



    def show_cancelled_treatments_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "cancelled_treatments"

        cancelled_items = [
            item
            for item in reversed(app_state.get("reservation_history", []))
            if item.get("status") in {"예약 취소", "노쇼"}
        ]
        cancelled_count = sum(1 for item in cancelled_items if item.get("status") == "예약 취소")
        no_show_count = sum(1 for item in cancelled_items if item.get("status") == "노쇼")

        def summary_tile(label, value, icon_name, color):
            return ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=14),
                bgcolor="#FFFCFA",
                border_radius=18,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=20, color=color),
                        ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(label, size=11, color=SUBTEXT_COLOR),
                    ],
                    spacing=3,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def cancelled_card(item):
            status = item.get("status", "예약 취소")
            is_no_show = status == "노쇼"
            accent = "#A15B43" if is_no_show else "#B85C5C"
            badge_text = "노쇼" if is_no_show else "취소"
            event_at = item.get("cancelled_at") or item.get("updated_at") or item.get("created_at") or ""

            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_XL,
                border=ft.border.all(1, BORDER_COLOR),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color="#0D000000",
                    offset=ft.Offset(0, 4),
                ),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=42,
                                    height=42,
                                    border_radius=999,
                                    bgcolor=ft.Colors.with_opacity(0.10, accent),
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(app_icon("EVENT_BUSY"), size=20, color=accent),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(item.get("artist_name", "취소된 시술"), size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                        ft.Text(item.get("job", ""), size=12, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    bgcolor=ft.Colors.with_opacity(0.10, accent),
                                    border_radius=999,
                                    content=ft.Text(badge_text, size=11, color=accent, weight=ft.FontWeight.W_700),
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=1, bgcolor=BORDER_COLOR),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CALENDAR_MONTH, size=15, color=MAIN_COLOR),
                                ft.Text(f'{item.get("date", "")} · {item.get("time", "")}', size=12, color=TEXT_COLOR),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(app_icon("CONTENT_CUT", "AUTO_FIX_HIGH"), size=15, color=MAIN_COLOR),
                                ft.Text(item.get("service", item.get("category", "기본 시술")), size=12, color=TEXT_COLOR),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            f"처리일: {event_at}" if event_at else "취소 또는 노쇼로 기록된 시술이에요.",
                            size=11,
                            color=SUBTEXT_COLOR,
                        ),
                    ],
                    spacing=10,
                ),
            )

        if cancelled_items:
            list_controls = [cancelled_card(item) for item in cancelled_items]
        else:
            list_controls = [
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=18, vertical=34),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                width=58,
                                height=58,
                                border_radius=999,
                                bgcolor=MAIN_COLOR_SOFT,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon("EVENT_AVAILABLE", "CHECK_CIRCLE_OUTLINE"), size=26, color=MAIN_COLOR),
                            ),
                            ft.Text("취소된 시술이 없어요", size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("취소와 노쇼 기록이 생기면 이곳에 정리돼요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ]

        body = ft.Column(
            controls=[
                page_header("취소된 시술", on_back=go_back_page),
                ft.Text("취소와 노쇼 기록을 한눈에 확인할 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Row(
                        controls=[
                            summary_tile("전체", len(cancelled_items), "EVENT_BUSY", MAIN_COLOR),
                            summary_tile("취소", cancelled_count, "CANCEL_OUTLINED", "#B85C5C"),
                            summary_tile("노쇼", no_show_count, "REPORT_PROBLEM_OUTLINED", "#A15B43"),
                        ],
                        spacing=8,
                    ),
                ),
                *list_controls,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_completed_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "completed"

        completed_items = []
        for item in reversed(app_state.get("reservation_history", [])):
            if item.get("status") == "예약 취소":
                continue
            date_value = item.get("date")
            time_value = item.get("time")
            is_past = False
            if date_value and time_value:
                try:
                    target_dt = reservation_datetime(date_value, time_value)
                    is_past = bool(target_dt and target_dt < datetime.now())
                except Exception:
                    is_past = False
            if item.get("status") == "시술 완료" or is_past:
                completed_items.append(item)

        cards = []
        if completed_items:
            for item in completed_items:
                cards.append(
                    browse_result_card(
                        {
                            "title": item.get("artist_name", "완료한 시술"),
                            "subtitle": item.get("job", ""),
                            "meta": f'{item.get("date", "")} · {item.get("time", "")}',
                            "description": f'시술: {item.get("service", item.get("category", ""))}\n상태: 방문 완료',
                            "badge": "완료",
                        }
                    )
                )
        else:
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("아직 완료한 시술이 없어요.", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("예약을 진행하고 방문이 끝나면 이곳에 기록이 쌓여요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                )
            )

        body = ft.Column(
            controls=[
                page_header("완료한 시술", on_back=go_back_page),
                ft.Text("방문이 끝난 시술 기록을 모아볼 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                *cards,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_beauty_profile_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "beauty_profile"

        profile = app_state.setdefault(
            "beauty_profile",
            {
                "style": "내추럴",
                "tone": "웜톤",
                "concern": "건조함",
                "memo": "평소 자연스러운 스타일을 선호해요.",
            },
        )

        def profile_chip(value, key):
            selected = profile.get(key) == value
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=MAIN_COLOR if selected else "#FFFFFF",
                border_radius=18,
                border=ft.border.all(1, MAIN_COLOR if selected else BORDER_COLOR),
                on_click=lambda e: (profile.__setitem__(key, value), show_beauty_profile_page()),
                ink=True,
                content=ft.Text(
                    value,
                    size=12,
                    color="#FFFFFF" if selected else TEXT_COLOR,
                    weight=ft.FontWeight.W_600,
                ),
            )

        memo_field = ft.TextField(
            width=content_width(),
            value=profile.get("memo", ""),
            multiline=True,
            min_lines=4,
            max_lines=6,
            hint_text="선호 스타일이나 고민을 자유롭게 적어주세요.",
            border_radius=16,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=16,
            on_change=lambda e: profile.__setitem__("memo", e.control.value or ""),
        )

        body = ft.Column(
            controls=[
                page_header("나의 뷰티 정보", on_back=go_back_page),
                ft.Text("선호하는 무드와 고민을 간단히 정리해둘 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("선호 스타일", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Row(
                                controls=[profile_chip("내추럴", "style"), profile_chip("러블리", "style"), profile_chip("세련됨", "style")],
                                wrap=True,
                                spacing=8,
                                run_spacing=8,
                            ),
                            ft.Container(height=6),
                            ft.Text("퍼스널 톤", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Row(
                                controls=[profile_chip("웜톤", "tone"), profile_chip("쿨톤", "tone"), profile_chip("뉴트럴", "tone")],
                                wrap=True,
                                spacing=8,
                                run_spacing=8,
                            ),
                            ft.Container(height=6),
                            ft.Text("현재 고민", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Row(
                                controls=[profile_chip("건조함", "concern"), profile_chip("손상모", "concern"), profile_chip("지속력", "concern")],
                                wrap=True,
                                spacing=8,
                                run_spacing=8,
                            ),
                            ft.Container(height=6),
                            ft.Text("메모", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            memo_field,
                        ],
                        spacing=10,
                    ),
                ),
                soft_button("저장했어요", MAIN_COLOR, "white", lambda e: show_snack("뷰티 정보가 반영되었어요.")),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_notice_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "notice"

        notices = [
            {
                "title": "FINDY 서비스 업데이트 안내",
                "subtitle": "최근 업데이트",
                "meta": "오늘",
                "description": "문의내역과 고객센터 기능이 추가되어 앱 안에서 더 쉽게 도움을 받을 수 있어요.",
                "badge": "NEW",
            },
            {
                "title": "예약 경험 개선 예정",
                "subtitle": "안내",
                "meta": "이번 주",
                "description": "더 빠른 예약 흐름과 맞춤형 추천 기능을 준비하고 있어요.",
                "badge": "NOTICE",
            },
        ]

        body = ft.Column(
            controls=[
                page_header("공지사항", on_back=go_back_page),
                ft.Text("서비스 운영 소식과 업데이트를 확인할 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                *[browse_result_card(item) for item in notices],
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_feedback_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "feedback"

        feedback_state = app_state.setdefault("feedback_form", {"content": ""})

        feedback_field = ft.TextField(
            width=content_width(),
            value=feedback_state.get("content", ""),
            multiline=True,
            min_lines=5,
            max_lines=8,
            hint_text="불편한 점, 추가되면 좋은 기능, 개선 아이디어를 자유롭게 적어주세요.",
            border_radius=16,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=16,
            on_change=lambda e: feedback_state.__setitem__("content", e.control.value or ""),
        )

        def submit_feedback(e):
            content = (feedback_state.get("content") or "").strip()
            if not content:
                show_snack("의견 내용을 입력해주세요.", bgcolor="#B85C5C")
                return
            app_state.setdefault("feedback_history", []).insert(
                0,
                {
                    "content": content,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
            )
            feedback_state["content"] = ""
            show_snack("개선 의견이 접수되었어요.")
            show_feedback_page()

        recent_feedback = app_state.get("feedback_history", [])[:3]
        history_controls = []
        for item in recent_feedback:
            history_controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(item.get("created_at", ""), size=11, color=SUBTEXT_COLOR),
                            ft.Text(item.get("content", ""), size=12, color=TEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                )
            )

        if not history_controls:
            history_controls.append(
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=24),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("아직 남긴 개선 의견이 없어요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            )

        body = ft.Column(
            controls=[
                page_header("개선 의견", on_back=go_back_page),
                ft.Text("더 나은 FINDY를 만들기 위한 아이디어를 들려주세요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                feedback_field,
                soft_button("의견 보내기", MAIN_COLOR, "white", submit_feedback),
                section_title("최근 남긴 의견", "앱 안에서 바로 확인할 수 있어요."),
                *history_controls,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_support_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "support"

        faq_items = [
            ("예약을 취소하고 싶어요", "예약내역에서 다가오는 예약을 선택하면 바로 취소할 수 있어요."),
            ("문의는 얼마나 빨리 답변되나요?", "운영시간 기준 순차적으로 확인하며 보통 1영업일 안에 답변드려요."),
            ("아티스트 정보가 실제와 다른가요?", "문의내역으로 알려주시면 확인 후 빠르게 반영할게요."),
        ]

        faq_controls = []
        for question, answer in faq_items:
            faq_controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(question, size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(answer, size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                )
            )

        body = ft.Column(
            controls=[
                page_header("고객센터", on_back=go_back_page),
                ft.Text("서비스 이용 중 궁금한 점을 빠르게 해결해보세요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("운영시간", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("평일 10:00 - 18:00", size=12, color=SUBTEXT_COLOR),
                            ft.Text("주말/공휴일에는 답변이 지연될 수 있어요.", size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=8),
                            ft.Text("문의 접수", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("문의내역 페이지에서 제목과 내용을 남기면 앱 안에서 바로 확인할 수 있어요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=6,
                    ),
                ),
                section_title("자주 묻는 질문", "가장 많이 문의하는 내용을 먼저 정리했어요."),
                *faq_controls,
                soft_button("1:1 문의하기", MAIN_COLOR, "white", lambda e: show_inquiry_page()),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_inquiry_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "inquiry"

        draft = app_state.setdefault(
            "inquiry_draft",
            {
                "category": "예약/결제",
                "title": "",
                "content": "",
            },
        )
        categories = ["예약/결제", "서비스 오류", "아티스트 제안", "기타"]

        title_field = ft.TextField(
            width=content_width(),
            value=draft.get("title", ""),
            hint_text="문의 제목을 입력해주세요.",
            border_radius=16,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=14,
            on_change=lambda e: draft.__setitem__("title", e.control.value or ""),
        )

        content_field = ft.TextField(
            width=content_width(),
            value=draft.get("content", ""),
            hint_text="문의 내용을 자세히 적어주세요.",
            multiline=True,
            min_lines=5,
            max_lines=8,
            border_radius=16,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=16,
            on_change=lambda e: draft.__setitem__("content", e.control.value or ""),
        )

        def choose_category(category):
            def handler(e):
                draft["category"] = category
                show_inquiry_page()
            return handler

        def submit_inquiry(e):
            title = (draft.get("title") or "").strip()
            content = (draft.get("content") or "").strip()
            if not title or not content:
                show_snack("제목과 내용을 모두 입력해주세요.", bgcolor="#B85C5C")
                return

            history = app_state.setdefault("inquiry_history", [])
            history.insert(
                0,
                {
                    "id": f"q{len(history) + 1}",
                    "category": draft.get("category") or "기타",
                    "title": title,
                    "content": content,
                    "status": "접수 완료",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
            )
            draft["title"] = ""
            draft["content"] = ""
            show_snack("문의가 접수되었어요.")
            show_inquiry_page()

        category_controls = [
            ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=MAIN_COLOR if draft.get("category") == category else "#FFFFFF",
                border_radius=18,
                border=ft.border.all(1, MAIN_COLOR if draft.get("category") == category else BORDER_COLOR),
                on_click=choose_category(category),
                ink=True,
                content=ft.Text(
                    category,
                    size=12,
                    color="#FFFFFF" if draft.get("category") == category else TEXT_COLOR,
                    weight=ft.FontWeight.W_600,
                ),
            )
            for category in categories
        ]

        history_controls = []
        for item in app_state.get("inquiry_history", []):
            history_controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(item.get("title", ""), size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, expand=True),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=CHIP_BG,
                                        border_radius=999,
                                        content=ft.Text(item.get("status", "접수 완료"), size=10, color=TEXT_COLOR),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(f'{item.get("category", "기타")} · {item.get("created_at", "")}', size=11, color=SUBTEXT_COLOR),
                            ft.Text(item.get("content", ""), size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                )
            )

        if not history_controls:
            history_controls.append(
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=24),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("아직 접수된 문의가 없어요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            )

        body = ft.Column(
            controls=[
                page_header("문의내역", on_back=go_back_page),
                ft.Text("문의 작성과 접수 내역 확인을 한 화면에서 할 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("문의 카테고리", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Row(controls=category_controls, wrap=True, spacing=8, run_spacing=8),
                            ft.Container(height=6),
                            ft.Text("문의 제목", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            title_field,
                            ft.Text("문의 내용", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            content_field,
                        ],
                        spacing=10,
                    ),
                ),
                soft_button("문의 접수하기", MAIN_COLOR, "white", submit_inquiry),
                section_title("접수된 문의", "최근에 남긴 문의를 바로 확인할 수 있어요."),
                *history_controls,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_notification_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 2
        app_state["current_page"] = "notifications"
        app_state["notification_read_at"] = datetime.now()
        items = reservation_notification_items()

        notice_list = [notification_card(item) for item in items]
        if not notice_list:
            notice_list = [
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=26),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("새로운 알림이 아직 없어요.", size=13, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            ]

        body = ft.Column(
            controls=[
                page_header("알림"),
                ft.Container(height=10),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("다가오는 예약과 상태 변경 알림을 모아봤어요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(height=12),
                *notice_list,
                ft.Container(height=18),
            ],
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_home_page():
        clear_transient_ui()
        if is_overlay_open("left"):
            app_state["selected_tab"] = 0
        elif is_overlay_open("right"):
            app_state["selected_tab"] = 4
        else:
            app_state["selected_tab"] = 2
        app_state["current_page"] = "home"

        def go_to_profile(e):
            app_state["selected_tab"] = 4
            show_my_page()

        def go_to_notice(e):
            open_notifications_page()

        async def transition_to_home_category(category_name):
            app_state["selected_category"] = category_name
            app_state["selected_tab"] = 2
            app_state["current_page"] = "home_category_transition"

            body = ft.Column(
                controls=[
                    ft.Container(expand=True),
                    ft.Container(
                        width=content_width(),
                        padding=ft.padding.symmetric(horizontal=24, vertical=30),
                        bgcolor="#FFFFFF",
                        border_radius=RADIUS_XL,
                        border=ft.border.all(1, BORDER_COLOR),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=18,
                            color="#12000000",
                            offset=ft.Offset(0, 6),
                        ),
                        content=ft.Column(
                            controls=[
                                ft.Container(
                                    width=58,
                                    height=58,
                                    border_radius=20,
                                    bgcolor=MAIN_COLOR_SOFT,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(
                                        app_icon("SEARCH", "EXPLORE"),
                                        size=26,
                                        color=MAIN_COLOR,
                                    ),
                                ),
                                ft.Text(category_name, size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ft.Text("원하는 스타일을 검색할 수 있게 준비 중이에요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                                ft.ProgressRing(width=30, height=30, color=MAIN_COLOR, stroke_width=3),
                            ],
                            spacing=12,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(expand=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )
            make_shell(body, app_state["selected_tab"])
            await asyncio.sleep(0.22)
            app_state["selected_category"] = category_name
            app_state["selected_tab"] = 2
            show_search_page()

        def go_to_category(category_name):
            def handler(e):
                page.run_task(transition_to_home_category, category_name)
            return handler

        def animated_block(content, y=0.04):
            return ft.Container(
                content=content,
                opacity=0,
                offset=ft.Offset(0, y),
                animate_opacity=ft.Animation(360, ft.AnimationCurve.EASE_OUT),
                animate_offset=ft.Animation(360, ft.AnimationCurve.EASE_OUT),
            )

        unread_count = unread_notification_count()
        badge_text = "9+" if unread_count > 9 else str(unread_count)
        bell_button = ft.Container(
            width=40,
            height=40,
            content=ft.Stack(
                controls=[
                    ft.IconButton(
                        icon=app_icon("NOTIFICATIONS_OUTLINED", "NOTIFICATIONS", "NOTIFICATION_ADD"),
                        icon_color=TEXT_COLOR,
                        icon_size=20,
                        tooltip="알림",
                        on_click=go_to_notice,
                    ),
                    ft.Container(
                        visible=unread_count > 0,
                        right=2,
                        top=2,
                        width=18 if unread_count < 10 else 22,
                        height=18,
                        border_radius=999,
                        bgcolor="#D97757",
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(badge_text, size=9, color="white", weight=ft.FontWeight.BOLD),
                    ),
                ]
            ),
        )

        header_logo_path = resolve_asset_file("findy_logo_horizontal.png")
        header_brand = (
            ft.Image(src=header_logo_path, width=164, height=36, fit=ft.ImageFit.CONTAIN)
            if header_logo_path
            else ft.Text("FINDY", size=28, weight=ft.FontWeight.BOLD, color=MAIN_COLOR)
        )

        header = ft.Container(
            width=content_width(),
            height=44,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=header_brand,
                    ),
                    ft.Container(
                        alignment=ft.Alignment(1, 0),
                        content=bell_button,
                    ),
                ]
            ),
        )

        global_search_field = ft.TextField(
            width=content_width() - 56,
            height=48,
            value=app_state.get("search_text", ""),
            hint_text="아티스트, 스냅, 리뷰, 예약 검색",
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.TRANSPARENT,
            cursor_color=MAIN_COLOR,
            text_size=13,
            color=TEXT_COLOR,
            hint_style=ft.TextStyle(color=SUBTEXT_COLOR, size=13),
            content_padding=ft.padding.only(left=16, right=8, top=12, bottom=12),
            on_submit=lambda e: submit_global_search(e.control.value),
        )

        global_search_bar = ft.Container(
            width=content_width(),
            height=52,
            bgcolor="#FFFFFF",
            border_radius=18,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color="#0C000000",
                offset=ft.Offset(0, 5),
            ),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=44,
                        height=44,
                        margin=ft.margin.only(left=6),
                        border_radius=14,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda e: submit_global_search(global_search_field.value),
                        content=ft.Icon(app_icon("SEARCH"), size=21, color=MAIN_COLOR),
                    ),
                    global_search_field,
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        slim_gap = 4
        search_category_block = ft.Container(
            width=content_width(),
            padding=8,
            bgcolor=ft.Colors.with_opacity(0.55, "#FFFFFF"),
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color="#0E000000",
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            category_square("CUT", "헤어", go_to_category("헤어")),
                            category_square("BRUSH", "네일아트", go_to_category("네일아트")),
                            category_square("FACE", "메이크업", go_to_category("메이크업")),
                        ],
                        spacing=slim_gap,
                    ),
                    ft.Row(
                        controls=[
                            category_square("AUTO_FIX_HIGH", "반영구시술", go_to_category("반영구시술")),
                            category_square("FAVORITE", "웨딩", go_to_category("웨딩")),
                            category_square("CAMERA_ALT", "포토", go_to_category("포토")),
                        ],
                        spacing=slim_gap,
                    ),
                ],
                spacing=slim_gap,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        upcoming_item = upcoming_reservations(limit=1)
        should_show_upcoming = bool(upcoming_item) and app_state.get("dismissed_upcoming_notice_id") != upcoming_item[0].get("id")
        upcoming_card = upcoming_reservation_floating_card(upcoming_item[0]) if should_show_upcoming else None

        hero_controls = [
            ft.Container(width=content_width(), content=header),
            ft.Container(height=8),
        ]
        if upcoming_card:
            hero_controls.extend([
                upcoming_card,
                ft.Container(height=12),
            ])
        hero_controls.extend([
            global_search_bar,
            ft.Container(height=12),
        ])
        hero_controls.append(search_category_block)

        hero_block = animated_block(
            ft.Column(
                controls=hero_controls,
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            y=0.03,
        )

        ad_block = animated_block(
            ft.Column(
                controls=[section_title("광고"), ad_banner()],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        snap_block = animated_block(
            ft.Column(
                controls=[
                    section_title("스냅", on_click=lambda e: go_snap_page()),
                    build_snap_carousel(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        review_block = animated_block(
            ft.Column(
                controls=[
                    section_title("리뷰", on_click=lambda e: show_review_page()),
                    build_review_carousel(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        animated_sections = [hero_block, ad_block, snap_block, review_block]

        body = ft.Column(
            controls=[
                hero_block,
                ft.Container(height=14),
                ad_block,
                ft.Container(height=16),
                snap_block,
                ft.Container(height=18),
                review_block,
                ft.Container(height=18),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

        async def animate_home_intro():
            await asyncio.sleep(0.02)
            for block in animated_sections:
                block.opacity = 1
                block.offset = ft.Offset(0, 0)
                page.update()
                await asyncio.sleep(0.05)

        if app_state.get("overlay") is None:
            page.run_task(animate_home_intro)
        else:
            for block in animated_sections:
                block.opacity = 1
                block.offset = ft.Offset(0, 0)

    def get_snap_feed_items(sort_mode, category_filter="헤어"):
        base_items = [
            {"id": "s01", "category": "헤어", "title": "레이어드 컷 스냅", "emoji": "📷", "accent": "#E8D9C8", "likes": 321, "saves": 144, "views": 2080, "ts": 21},
            {"id": "s02", "category": "메이크업", "title": "윤광 베이스 스냅", "emoji": "💄", "accent": "#D9C6B0", "likes": 287, "saves": 120, "views": 1960, "ts": 20},
            {"id": "s03", "category": "헤어", "title": "빌드펌 무드컷", "emoji": "✨", "accent": "#E9E1D7", "likes": 355, "saves": 163, "views": 2540, "ts": 19},
            {"id": "s04", "category": "메이크업", "title": "웨딩 피치 메이크업", "emoji": "👰", "accent": "#E3D2C6", "likes": 274, "saves": 152, "views": 1830, "ts": 18},
            {"id": "s05", "category": "헤어", "title": "드라이 볼륨 스냅", "emoji": "📸", "accent": "#D7C1AC", "likes": 238, "saves": 94, "views": 1715, "ts": 17},
            {"id": "s06", "category": "헤어", "title": "내추럴 브라운 컬러", "emoji": "🌿", "accent": "#E8DED2", "likes": 264, "saves": 111, "views": 1880, "ts": 16},
            {"id": "s07", "category": "네일아트", "title": "글로시 핑크 네일", "emoji": "💅", "accent": "#E5D3C0", "likes": 296, "saves": 138, "views": 1940, "ts": 15},
            {"id": "s08", "category": "메이크업", "title": "데일리 소프트 음영", "emoji": "🪞", "accent": "#E6DBCF", "likes": 181, "saves": 76, "views": 1490, "ts": 14},
            {"id": "s09", "category": "네일아트", "title": "화이트 프렌치 네일", "emoji": "🤍", "accent": "#EFE6DC", "likes": 334, "saves": 166, "views": 2210, "ts": 13},
            {"id": "s10", "category": "헤어", "title": "시크 블랙 단발", "emoji": "🖤", "accent": "#D9CEC1", "likes": 205, "saves": 88, "views": 1605, "ts": 12},
            {"id": "s11", "category": "네일아트", "title": "무드 파츠 네일", "emoji": "🎞️", "accent": "#E0D2C5", "likes": 190, "saves": 81, "views": 1580, "ts": 11},
            {"id": "s12", "category": "메이크업", "title": "봄 라이트 메이크업", "emoji": "🌸", "accent": "#EADFD6", "likes": 242, "saves": 109, "views": 1765, "ts": 10},
            {"id": "s13", "category": "네일아트", "title": "클라우드 시럽 네일", "emoji": "☁️", "accent": "#E5E0D8", "likes": 173, "saves": 74, "views": 1420, "ts": 9},
            {"id": "s14", "category": "메이크업", "title": "로지 포인트 메이크업", "emoji": "💫", "accent": "#E4D6C8", "likes": 226, "saves": 101, "views": 1680, "ts": 8},
            {"id": "s15", "category": "네일아트", "title": "리본 포인트 네일", "emoji": "🎀", "accent": "#E7D7CA", "likes": 309, "saves": 142, "views": 2125, "ts": 7},
            {"id": "s16", "category": "포토", "title": "감성 프로필 포토", "emoji": "📷", "accent": "#DDD1C6", "likes": 278, "saves": 117, "views": 1895, "ts": 6},
            {"id": "s17", "category": "웨딩", "title": "브라이드 무드 스냅", "emoji": "💍", "accent": "#E8DDD6", "likes": 366, "saves": 171, "views": 2610, "ts": 5},
            {"id": "s18", "category": "반영구", "title": "자연눈썹 시술 스냅", "emoji": "✨", "accent": "#DCCCBD", "likes": 214, "saves": 96, "views": 1665, "ts": 4},
            {"id": "s19", "category": "포토", "title": "데일리 무드 촬영", "emoji": "🖼️", "accent": "#E6DDD4", "likes": 247, "saves": 104, "views": 1738, "ts": 3},
            {"id": "s20", "category": "웨딩", "title": "본식 헤어메이크업 스냅", "emoji": "👰", "accent": "#EBD9D2", "likes": 302, "saves": 145, "views": 2188, "ts": 2},
            {"id": "s21", "category": "반영구", "title": "아이라인 포인트 스냅", "emoji": "🪄", "accent": "#E2D4C8", "likes": 198, "saves": 89, "views": 1525, "ts": 1},
        ]

        items = [item.copy() for item in base_items if item["category"] == category_filter]
        if sort_mode == "popular":
            items.sort(key=lambda x: x["views"], reverse=True)
        elif sort_mode == "recommended":
            items.sort(key=lambda x: (x["likes"] + x["saves"] * 2), reverse=True)
        else:
            items.sort(key=lambda x: x["ts"], reverse=True)
        return items

    def snap_layout_selector_button(mode, selected_mode, on_click):
        active = mode == selected_mode
        accent = MAIN_COLOR_DARK if active else SUBTEXT_COLOR

        if mode == 1:
            icon_content = ft.Column(
                controls=[
                    ft.Container(width=14, height=2.5, border_radius=1, bgcolor=accent),
                    ft.Container(width=14, height=2.5, border_radius=1, bgcolor=accent),
                    ft.Container(width=14, height=2.5, border_radius=1, bgcolor=accent),
                ],
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            def dot():
                return ft.Container(width=4, height=4, border_radius=1, bgcolor=accent)
            icon_content = ft.Column(
                controls=[
                    ft.Row(controls=[dot(), dot(), dot()], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row(controls=[dot(), dot(), dot()], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        return ft.Container(
            width=30,
            height=30,
            bgcolor="#FFFDFC" if active else ft.Colors.TRANSPARENT,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color="#0A8B6B4F",
                offset=ft.Offset(0, 3),
            ) if active else None,
            on_click=on_click,
            ink=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            alignment=ft.Alignment(0, 0),
            content=icon_content,
        )

    def snap_sort_chip(label, key):
        active = app_state.get("snap_sort_mode") == key

        def handle(e):
            app_state["snap_sort_mode"] = key
            show_snap_page()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            bgcolor="#F7F0E9" if active else "#FFFDFC",
            border_radius=999,
            border=ft.border.all(1, MAIN_COLOR if active else ft.Colors.with_opacity(0.76, BORDER_COLOR)),
            on_click=handle,
            ink=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            content=ft.Text(
                label,
                size=12,
                color=MAIN_COLOR_DARK if active else TEXT_COLOR,
                weight=ft.FontWeight.W_500 if active else ft.FontWeight.W_400,
            ),
        )

    def snap_category_filter_chip(label):
        active = app_state.get("snap_filter", "헤어") == label

        def handle(e):
            app_state["snap_filter"] = label
            show_snap_page()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            bgcolor="#F7F0E9" if active else "#FFFDFC",
            border_radius=999,
            border=ft.border.all(1, MAIN_COLOR if active else ft.Colors.with_opacity(0.76, BORDER_COLOR)),
            on_click=handle,
            ink=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            content=ft.Text(
                label,
                size=12,
                color=MAIN_COLOR_DARK if active else TEXT_COLOR,
                weight=ft.FontWeight.W_500 if active else ft.FontWeight.W_400,
            ),
        )

    def open_snap_detail(item):
        app_state["snap_detail_item"] = item
        show_snap_detail_page()

    def treatment_artist_options(preferred_item=None):
        options = []
        seen_ids = set()
        candidates = []
        if preferred_item:
            candidates.append(preferred_item)
        candidates.extend(list(reversed(app_state.get("reservation_history", []))))
        for candidate in candidates:
            reservation_id = candidate.get("id")
            if reservation_id in seen_ids:
                continue
            if classify_history_item(candidate) == "past" or candidate.get("status") == "시술 완료" or candidate == preferred_item:
                options.append(candidate)
                seen_ids.add(reservation_id)
        return options

    def build_artist_selection_panel(selected_item, options, selected_artist_text, selected_meta_text, option_controls):
        def refresh():
            current = selected_item[0]
            selected_artist_text.value = current.get("artist_name", "")
            selected_meta_text.value = f'{current.get("service", current.get("category", ""))}  ·  {current.get("date", "")}'
            for control, option in option_controls:
                active = option.get("id") == current.get("id")
                control.bgcolor = MAIN_COLOR if active else "#FFFFFF"
                control.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
                control.content.controls[0].color = "#FFFFFF" if active else TEXT_COLOR
                control.content.controls[1].color = "#FFFFFF" if active else SUBTEXT_COLOR

        def select(option):
            def handler(e):
                selected_item[0] = option
                refresh()
                page.update()
            return handler

        option_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
        for option in options:
            option_card = ft.Container(
                width=142,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=14,
                ink=True,
                on_click=select(option),
                content=ft.Column(
                    controls=[
                        ft.Text(option.get("artist_name", ""), size=12, weight=ft.FontWeight.W_600, max_lines=1),
                        ft.Text(option.get("service", option.get("category", "")), size=10, max_lines=1),
                    ],
                    spacing=3,
                ),
            )
            option_controls.append((option_card, option))
            option_row.controls.append(option_card)

        refresh()
        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Text("시술받은 아티스트", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                    ft.Container(height=4),
                    ft.Row(
                        controls=[
                            ft.Container(width=42, height=42, border_radius=14, bgcolor="#000000"),
                            ft.Column(controls=[selected_artist_text, selected_meta_text], spacing=3, expand=True),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),
                    option_row,
                ],
                spacing=0,
            ),
        )

    def snap_photo_tile(item, width, height, layout_mode=1):
        tile = ft.Container(
            width=width,
            height=height,
            border_radius=4,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            content=ft.Stack(
                controls=[
                    black_image_box(width, height),
                    ft.Container(
                        left=8,
                        top=8,
                        padding=ft.padding.symmetric(horizontal=7, vertical=4),
                        bgcolor=ft.Colors.with_opacity(0.7, "#FFFFFF"),
                        border_radius=10,
                        content=ft.Icon(ft.Icons.PHOTO_LIBRARY, size=12, color=TEXT_COLOR),
                    ),
                    (
                        ft.Container(
                            bottom=8,
                            left=8,
                            right=8,
                            alignment=ft.Alignment(1, 0),
                            content=ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor="#FFFFFF",
                                border_radius=12,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.FAVORITE_BORDER, size=12, color=TEXT_COLOR),
                                        ft.Text(str(item["likes"]), size=10, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                                    ],
                                    spacing=4,
                                    tight=True,
                                ),
                            ),
                        )
                        if layout_mode == 3 else
                        ft.Container(
                            left=8,
                            bottom=8,
                            right=8,
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                        bgcolor="#FFFFFF",
                                        border_radius=0,
                                        content=ft.Column(
                                            controls=[
                                                ft.Text(item.get("category", "스냅"), size=9, color=SUBTEXT_COLOR),
                                                ft.Text(item.get("title", "스냅"), size=10, color=TEXT_COLOR, max_lines=1),
                                            ],
                                            spacing=1,
                                        ),
                                    ),
                                    ft.Container(expand=True),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                        bgcolor="#FFFFFF",
                                        border_radius=0,
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.FAVORITE_BORDER, size=10, color=TEXT_COLOR),
                                                ft.Text(str(item["likes"]), size=10, color=TEXT_COLOR),
                                            ],
                                            spacing=4,
                                            tight=True,
                                        ),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.END,
                            ),
                        )
                    ),
                ]
            ),
        )

        def tap_down(e):
            tile.scale = 1.04
            page.update()

        def tap_up(e):
            tile.scale = 1.0
            page.update()

        def tap(e):
            tile.scale = 1.0
            page.update()
            open_snap_detail(item)

        return ft.GestureDetector(
            on_tap_down=tap_down,
            on_tap_up=tap_up,
            on_tap=tap,
            content=tile,
        )

    def build_snap_feed(layout_mode, sort_mode, category_filter):
        items = get_snap_feed_items(sort_mode, category_filter)
        user_items = [
            snap.copy()
            for snap in app_state.get("written_snaps", [])
            if snap.get("category") == category_filter
        ]
        items = user_items + items
        controls = []

        def pad_row(row_controls, total_cols, card_w, card_h):
            while len(row_controls) < total_cols:
                row_controls.append(ft.Container(width=card_w, height=card_h, opacity=0))
            return row_controls

        if layout_mode == 1:
            card_w = PHONE_WIDTH
            card_h = int(card_w * 5 / 4)  # 4:5
            for item in items:
                controls.append(
                    ft.Row(
                        width=full_phone_width(),
                        controls=[snap_photo_tile(item, card_w, card_h, layout_mode=1)],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.START,
                    )
                )

        elif layout_mode == 3:
            card_w = PHONE_WIDTH // 3
            card_h = int(card_w * 5 / 4)  # 4:5
            for i in range(0, len(items), 3):
                row_items = items[i:i+3]
                row_controls = [snap_photo_tile(item, card_w, card_h, layout_mode=3) for item in row_items]
                controls.append(
                    ft.Row(
                        width=full_phone_width(),
                        controls=pad_row(row_controls, 3, card_w, card_h),
                        spacing=0,
                        alignment=ft.MainAxisAlignment.START,
                    )
                )

        return ft.Container(
            width=full_phone_width(),
            content=ft.Column(
                controls=controls,
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def tab_page_intro(title, subtitle):
        section_logo_path = resolve_asset_file("findy_logo_horizontal.png")
        section_logo = (
            ft.Image(src=section_logo_path, width=120, height=28, fit=ft.ImageFit.CONTAIN)
            if section_logo_path
            else ft.Text("FINDY", size=28, weight=ft.FontWeight.W_800, color=MAIN_COLOR)
        )
        return ft.Container(
            width=content_width(),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            section_logo,
                            ft.Text(title, size=25, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                        ],
                        spacing=9,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(subtitle, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        margin=ft.margin.only(top=10),
                        border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                    ),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def show_snap_page():
        clear_transient_ui()
        app_state["selected_tab"] = 1
        app_state["current_page"] = "snap"

        def choose_layout(mode):
            def handler(e):
                app_state["snap_layout_mode"] = mode
                show_snap_page()
            return handler

        layout_toggle = ft.Container(
            padding=ft.padding.all(3),
            bgcolor=CHIP_BG,
            border_radius=12,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Row(
                controls=[
                    snap_layout_selector_button(1, app_state.get("snap_layout_mode", 3), choose_layout(1)),
                    snap_layout_selector_button(3, app_state.get("snap_layout_mode", 3), choose_layout(3)),
                ],
                spacing=4,
            ),
        )

        sort_row = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            snap_sort_chip("인기순", "popular"),
                            snap_sort_chip("최신순", "latest"),
                            snap_sort_chip("추천순", "recommended"),
                        ],
                        spacing=6,
                    ),
                    layout_toggle,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        category_chip_row = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[
                    snap_category_filter_chip("헤어"),
                    snap_category_filter_chip("네일아트"),
                    snap_category_filter_chip("메이크업"),
                    snap_category_filter_chip("반영구"),
                    snap_category_filter_chip("웨딩"),
                    snap_category_filter_chip("포토"),
                ],
                spacing=8,
                scroll=ft.ScrollMode.HIDDEN,
            ),
        )

        body = ft.Column(
            controls=[
                tab_page_intro("스냅", "원하는 스타일을 빠르게 둘러보고 저장해보세요."),
                ft.Container(height=12),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
                    on_click=lambda e: (app_state.__setitem__("current_page", "write_snap"), show_write_snap_page()),
                    ink=True,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, size=18, color=MAIN_COLOR),
                            ft.Text("시술받은 아티스트로 스냅 작성", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=10),
                sort_row,
                ft.Container(height=8),
                category_chip_row,
                ft.Container(height=10),
                build_snap_feed(
                    app_state.get("snap_layout_mode", 3),
                    app_state.get("snap_sort_mode", "popular"),
                    app_state.get("snap_filter", "헤어"),
                ),
                ft.Container(height=20),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
        )

        make_shell(body, app_state["selected_tab"])

    def show_write_snap_page():
        close_overlays()
        app_state["selected_tab"] = 1
        app_state["current_page"] = "write_snap"

        options = treatment_artist_options()
        if not options:
            body = ft.Column(
                controls=[
                    page_header("스냅 작성", on_back=lambda e: show_snap_page()),
                    ft.Container(
                        width=content_width(),
                        padding=SPACE_XL,
                        bgcolor="#FFFFFF",
                        border_radius=RADIUS_XL,
                        border=ft.border.all(1, BORDER_COLOR),
                        content=ft.Column(
                            controls=[
                                ft.Text("선택할 수 있는 시술 내역이 없어요.", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ft.Text("시술이 완료된 예약이 있으면 아티스트를 선택해 스냅을 남길 수 있어요.", size=12, color=SUBTEXT_COLOR),
                            ],
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            make_shell(body, app_state["selected_tab"])
            return

        selected_item = [options[0]]
        selected_artist_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
        selected_meta_text = ft.Text("", size=12, color=SUBTEXT_COLOR)
        option_controls = []
        artist_panel = build_artist_selection_panel(selected_item, options, selected_artist_text, selected_meta_text, option_controls)

        title_field = ft.TextField(
            width=content_width(),
            hint_text="예: 브라이드 무드 스냅",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        note_field = ft.TextField(
            width=content_width(),
            hint_text="사진 분위기나 시술 포인트를 짧게 남겨주세요.",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )

        def submit_snap(e):
            current = selected_item[0]
            title = (title_field.value or "").strip()
            note = (note_field.value or "").strip()
            if not title:
                show_snack("스냅 제목을 입력해주세요.", bgcolor="#B85C5C")
                return
            snap = {
                "id": f"user_{len(app_state.get('written_snaps', [])) + 1}",
                "category": current.get("category", "스냅"),
                "title": title,
                "artist_id": current.get("artist_id"),
                "artist_name": current.get("artist_name", ""),
                "service": current.get("service", current.get("category", "")),
                "description": note,
                "emoji": "📷",
                "likes": 0,
                "saves": 0,
                "views": 0,
                "ts": 999 + len(app_state.get("written_snaps", [])),
            }
            app_state.setdefault("written_snaps", []).insert(0, snap)
            app_state["snap_filter"] = snap["category"]
            show_snack("스냅이 등록되었어요.")
            show_snap_page()

        body = ft.Column(
            controls=[
                page_header("스냅 작성", on_back=lambda e: show_snap_page()),
                artist_panel,
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("스냅 제목", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            title_field,
                            ft.Container(height=12),
                            ft.Text("설명", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            note_field,
                        ],
                        spacing=0,
                    ),
                ),
                soft_button("스냅 등록", MAIN_COLOR, "white", submit_snap, width=content_width()),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def snap_detail_stat(label, value, icon_name, compact=False, value_control=None):
        return ft.Container(
            width=68 if compact else None,
            expand=None if compact else True,
            padding=ft.padding.symmetric(vertical=9 if compact else 10),
            bgcolor=ft.Colors.with_opacity(0.68, "#FFFFFF"),
            border_radius=RADIUS_MD,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Icon(app_icon(icon_name), size=16 if compact else 18, color=MAIN_COLOR),
                    value_control or ft.Text(str(value), size=13 if compact else 14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text(label, size=10, color=SUBTEXT_COLOR),
                ],
                spacing=3 if compact else 4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def snap_detail_thumbnail(item, index):
        return ft.Container(
            width=100,
            height=100,
            border_radius=4,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                controls=[
                    black_image_box(100, 100),
                    ft.Container(
                        right=8,
                        bottom=8,
                        padding=ft.padding.symmetric(horizontal=7, vertical=3),
                        bgcolor=ft.Colors.with_opacity(0.80, "#FFFFFF"),
                        border_radius=10,
                        content=ft.Text(f"컷 {index}", size=10, color=TEXT_COLOR),
                    ),
                ]
            ),
        )

    def show_snap_detail_page():
        clear_transient_ui()
        item = app_state.get("snap_detail_item")
        if not item:
            show_snap_page()
            return

        if is_overlay_open("left"):
            app_state["selected_tab"] = 0
        elif is_overlay_open("right"):
            app_state["selected_tab"] = 4
        else:
            app_state["selected_tab"] = 1
        app_state["current_page"] = "snap_detail"

        related_items = [x for x in get_snap_feed_items(app_state.get("snap_sort_mode", "popular"), app_state.get("snap_filter", "헤어")) if x["id"] != item["id"]][:6]
        item_id = item["id"]
        like_count_text = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
        save_count_text = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
        like_icon = ft.Icon(size=15)
        like_label = ft.Text("좋아요", size=13)
        save_icon = ft.Icon(size=15)
        save_label = ft.Text("저장", size=13)
        like_button = ft.Container(width=86, height=38, border_radius=999, alignment=ft.Alignment(0, 0))
        save_button = ft.Container(width=86, height=38, border_radius=999, alignment=ft.Alignment(0, 0))
        like_button.content = ft.Row(
            controls=[like_icon, like_label],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        save_button.content = ft.Row(
            controls=[save_icon, save_label],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        def refresh_snap_action_controls():
            liked = item_id in app_state.get("snap_liked_ids", set())
            saved = item_id in app_state.get("snap_saved_ids", set())

            like_count_text.value = str(item["likes"] + (1 if liked else 0))
            save_count_text.value = str(item["saves"] + (1 if saved else 0))

            like_button.bgcolor = MAIN_COLOR if liked else "#FFFFFF"
            like_button.border = ft.border.all(1, MAIN_COLOR if liked else BORDER_COLOR)
            like_icon.name = ft.Icons.FAVORITE if liked else ft.Icons.FAVORITE_BORDER
            like_icon.color = "#FFFFFF" if liked else SUBTEXT_COLOR
            like_label.color = "#FFFFFF" if liked else SUBTEXT_COLOR

            save_button.bgcolor = MAIN_COLOR_SOFT if saved else "#FFFFFF"
            save_button.border = ft.border.all(1, MAIN_COLOR if saved else BORDER_COLOR)
            save_icon.name = ft.Icons.BOOKMARK if saved else ft.Icons.BOOKMARK_BORDER
            save_icon.color = MAIN_COLOR if saved else SUBTEXT_COLOR
            save_label.color = MAIN_COLOR if saved else SUBTEXT_COLOR

        def update_snap_action_controls():
            for control in [like_count_text, save_count_text, like_button, save_button]:
                try:
                    control.update()
                except Exception:
                    pass

        def toggle_snap_like(e):
            liked_ids = app_state.setdefault("snap_liked_ids", set())
            if item_id in liked_ids:
                liked_ids.discard(item_id)
            else:
                liked_ids.add(item_id)
            refresh_snap_action_controls()
            update_snap_action_controls()

        def toggle_snap_save(e):
            saved_ids = app_state.setdefault("snap_saved_ids", set())
            if item_id in saved_ids:
                saved_ids.discard(item_id)
            else:
                saved_ids.add(item_id)
            refresh_snap_action_controls()
            update_snap_action_controls()

        refresh_snap_action_controls()

        body = ft.Column(
            controls=[
                page_header("스냅"),
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            ft.Container(expand=True),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=7),
                                bgcolor="#FFFFFF",
                                border_radius=4,
                                content=ft.Text("SNAP DETAIL", size=10, color=SUBTEXT_COLOR),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    height=260,
                    border_radius=30,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Stack(
                        controls=[
                            black_image_box(content_width(), 260),
                            ft.Container(
                                right=14,
                                bottom=14,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=ft.Colors.with_opacity(0.75, "#FFFFFF"),
                                border_radius=8,
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.REMOVE_RED_EYE_OUTLINED, size=13, color=TEXT_COLOR),
                                        ft.Text(str(item["views"]), size=10, color=TEXT_COLOR),
                                    ],
                                    spacing=5,
                                ),
                            ),
                        ]
                    ),
                ),
                ft.Container(height=14),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=16,
                        color="#0E000000",
                        offset=ft.Offset(0, 5),
                    ),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(item["title"], size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, expand=True),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        bgcolor=MAIN_COLOR_SOFT,
                                        border_radius=999,
                                        content=ft.Text(item["category"], size=11, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                f'{item.get("artist_name", "")} · {item.get("service", "")}' if item.get("artist_name") else "",
                                size=12,
                                color=SUBTEXT_COLOR,
                                visible=bool(item.get("artist_name")),
                            ),
                            ft.Container(height=10),
                            ft.Text("관련 스냅", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Container(height=6),
                            ft.Row(
                                controls=[snap_detail_thumbnail(thumb, idx + 1) for idx, thumb in enumerate(related_items[:3])],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[snap_detail_thumbnail(thumb, idx + 4) for idx, thumb in enumerate(related_items[3:6])],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(height=14),
                            ft.Row(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            snap_detail_stat("조회", item["views"], "REMOVE_RED_EYE_OUTLINED", compact=True),
                                            snap_detail_stat("좋아요", item["likes"], "FAVORITE_BORDER", compact=True, value_control=like_count_text),
                                            snap_detail_stat("저장", item["saves"], "BOOKMARK_BORDER", compact=True, value_control=save_count_text),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.GestureDetector(on_tap=toggle_snap_like, content=like_button),
                                            ft.GestureDetector(on_tap=toggle_snap_save, content=save_button),
                                        ],
                                        spacing=8,
                                    ),
                                ],
                                spacing=8,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=0,
                    ),
                ),
                ft.Container(height=16),
                ft.GestureDetector(
                    on_tap=lambda e: [
                        app_state.__setitem__("selected_category", item["category"]),
                        app_state.__setitem__("selected_subcategory", "아티스트"),
                        app_state.__setitem__("search_results", build_category_browse_items(item["category"], "아티스트")),
                        app_state.__setitem__("recommendation_entry", item["category"]),
                        app_state.__setitem__("category_browse_mode", True),
                        app_state.__setitem__("search_results_back_target", "snap_detail"),
                        app_state.__setitem__("current_page", "search_results"),
                        render_current_page(),
                    ],
                    content=ft.Container(
                        width=content_width(),
                        padding=ft.padding.symmetric(vertical=14),
                        bgcolor=MAIN_COLOR,
                        border_radius=RADIUS_LG,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("아티스트 정보", size=14, color="white", weight=ft.FontWeight.BOLD),
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_video_page():
        clear_transient_ui()
        app_state["selected_tab"] = 3
        app_state["current_page"] = "video"

        video_categories = ["전체", "헤어", "메이크업", "네일아트", "웨딩", "포토"]
        selected_cat = app_state.get("video_category_filter", "전체")

        all_videos = [
            {"title": "레이어드컷 완성 과정", "subtitle": "자연스럽게 층 내는 법 총정리", "badge": "SHORTS", "category": "헤어", "duration": "0:58", "views": "3.2만"},
            {"title": "빌드펌 시술 타임랩스", "subtitle": "굵은 웨이브 연출 풀영상", "badge": "REELS", "category": "헤어", "duration": "1:12", "views": "2.8만"},
            {"title": "윤광 베이스 메이크업", "subtitle": "5분 완성 데일리 베이스", "badge": "SHORTS", "category": "메이크업", "duration": "0:52", "views": "4.1만"},
            {"title": "웨딩 피치 메이크업 풀버전", "subtitle": "본식 당일 메이크업 과정", "badge": "TREND", "category": "메이크업", "duration": "2:30", "views": "5.6만"},
            {"title": "글로시 핑크 네일 시술", "subtitle": "아이디어가 되는 네일 무드", "badge": "SHORTS", "category": "네일아트", "duration": "0:45", "views": "2.1만"},
            {"title": "파츠 아트 네일 디테일컷", "subtitle": "트렌드 파츠 배치 영상", "badge": "REELS", "category": "네일아트", "duration": "1:05", "views": "1.9만"},
            {"title": "브라이드 무드 헤어메이크업", "subtitle": "본식 스타일링 하이라이트", "badge": "TREND", "category": "웨딩", "duration": "2:15", "views": "6.3만"},
            {"title": "하객 스타일링 루틴", "subtitle": "결혼식 참석룩 완성하기", "badge": "SHORTS", "category": "웨딩", "duration": "1:08", "views": "3.7만"},
            {"title": "감성 프로필 포토 촬영 BTS", "subtitle": "자연광 촬영 세팅 공개", "badge": "REELS", "category": "포토", "duration": "1:40", "views": "2.5만"},
            {"title": "데일리 무드 셀프 촬영법", "subtitle": "폰으로 찍는 감성 포토 팁", "badge": "TREND", "category": "포토", "duration": "2:00", "views": "4.4만"},
        ]
        all_videos = list(app_state.get("written_videos", [])) + all_videos

        filtered = all_videos if selected_cat == "전체" else [v for v in all_videos if v["category"] == selected_cat]

        def choose_cat(cat):
            def handler(e):
                app_state["video_category_filter"] = cat
                show_video_page()
            return handler

        def video_card(v):
            return ft.Container(
                width=content_width(),
                height=186,
                border_radius=28,
                bgcolor="#FFFDFC",
                border=ft.border.all(1, ft.Colors.with_opacity(0.76, BORDER_COLOR)),
                padding=SPACE_LG,
                on_click=lambda e: show_snack(f"'{v['title']}' 영상은 준비 중이에요."),
                ink=True,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color="#0D8B6B4F",
                    offset=ft.Offset(0, 9),
                ),
                content=ft.Stack(
                    controls=[
                        ft.Container(
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL_ROUNDED, size=54, color=MAIN_COLOR),
                        ),
                        ft.Container(
                            left=0,
                            top=0,
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        border_radius=999,
                                        bgcolor="#F7F0E9",
                                        border=ft.border.all(1, "#EFE4D9"),
                                        content=ft.Text(v["badge"], size=10, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        border_radius=999,
                                        bgcolor="#FFFDFC",
                                        border=ft.border.all(1, "#EFE4D9"),
                                        content=ft.Text(v["category"], size=10, color=MAIN_COLOR),
                                    ),
                                ],
                                spacing=6,
                            ),
                        ),
                        ft.Container(
                            left=0,
                            right=0,
                            bottom=0,
                            content=ft.Column(
                                controls=[
                                    ft.Text(v["title"], size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ft.Row(
                                        controls=[
                                            ft.Text(v["subtitle"], size=12, color=SUBTEXT_COLOR, expand=True),
                                            ft.Text(f"{v['duration']}  조회 {v['views']}", size=11, color=SUBTEXT_COLOR),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                ],
                                spacing=4,
                            ),
                        ),
                    ]
                ),
            )

        cat_chips = ft.Row(
            controls=[
                ft.GestureDetector(
                    on_tap=choose_cat(cat),
                    content=ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        bgcolor="#F7F0E9" if cat == selected_cat else "#FFFDFC",
                        border_radius=999,
                        border=ft.border.all(1, MAIN_COLOR if cat == selected_cat else ft.Colors.with_opacity(0.76, BORDER_COLOR)),
                        content=ft.Text(cat, size=12, color=MAIN_COLOR_DARK if cat == selected_cat else TEXT_COLOR, weight=ft.FontWeight.W_600 if cat == selected_cat else ft.FontWeight.NORMAL),
                    ),
                )
                for cat in video_categories
            ],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
        )

        write_video_button = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor="#FFFDFC",
            border_radius=24,
            border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=14, color="#0A8B6B4F", offset=ft.Offset(0, 6)),
            on_click=lambda e: (app_state.__setitem__("current_page", "write_video"), show_write_video_page()),
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.VIDEO_CALL_OUTLINED, size=20, color=MAIN_COLOR),
                    ft.Column(
                        controls=[
                            ft.Text("영상 올리기", size=14, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                            ft.Text("비디오 페이지에는 영상만 등록할 수 있어요.", size=11, color=ft.Colors.with_opacity(0.75, MAIN_COLOR)),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        body = ft.Column(
            controls=[
                tab_page_intro("비디오", "짧고 감도 높은 스타일 영상을 모아봤어요."),
                ft.Container(height=10),
                write_video_button,
                ft.Container(
                    width=content_width(),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=cat_chips,
                ),
                ft.Container(height=8),
                *[video_card(v) for v in filtered],
                ft.Container(height=18),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_write_video_page():
        close_overlays()
        app_state["selected_tab"] = 3
        app_state["current_page"] = "write_video"

        selected_category = [app_state.get("video_category_filter", "전체")]
        if selected_category[0] == "전체":
            selected_category[0] = "헤어"
        selected_video_path = [None]
        video_name_text = ft.Text("선택된 영상이 없어요.", size=12, color=SUBTEXT_COLOR)

        title_field = ft.TextField(
            width=content_width(),
            hint_text="영상 제목을 입력해주세요.",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        subtitle_field = ft.TextField(
            width=content_width(),
            hint_text="짧은 설명을 입력해주세요.",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )

        category_controls = []

        def refresh_category_controls():
            for control, category in category_controls:
                active = selected_category[0] == category
                control.bgcolor = MAIN_COLOR if active else CHIP_BG
                control.content.color = "#FFFFFF" if active else TEXT_COLOR

        def choose_category(category):
            def handler(e):
                selected_category[0] = category
                refresh_category_controls()
                page.update()
            return handler

        category_row = ft.Row(spacing=6, scroll=ft.ScrollMode.AUTO)
        for category in ["헤어", "메이크업", "네일아트", "웨딩", "포토"]:
            chip_control = ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                border_radius=999,
                on_click=choose_category(category),
                ink=True,
                content=ft.Text(category, size=12, weight=ft.FontWeight.W_600),
            )
            category_controls.append((chip_control, category))
            category_row.controls.append(chip_control)
        refresh_category_controls()

        def on_video_picked(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            selected_file = e.files[0]
            selected_video_path[0] = selected_file.path or selected_file.name
            video_name_text.value = selected_file.name
            page.update()

        file_picker = ft.FilePicker(on_result=on_video_picked)
        page.overlay.append(file_picker)
        page.update()

        def cleanup_file_picker():
            if file_picker in page.overlay:
                page.overlay.remove(file_picker)

        def pick_video(e):
            file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["mp4", "mov", "m4v", "webm"],
            )

        def go_back(e=None):
            cleanup_file_picker()
            show_video_page()

        def submit_video(e):
            title = (title_field.value or "").strip()
            subtitle = (subtitle_field.value or "").strip()
            if not selected_video_path[0]:
                show_snack("영상을 선택해주세요.", bgcolor="#B85C5C")
                return
            if not title:
                show_snack("영상 제목을 입력해주세요.", bgcolor="#B85C5C")
                return
            app_state.setdefault("written_videos", []).insert(0, {
                "title": title,
                "subtitle": subtitle or "업로드한 스타일 영상",
                "badge": "UPLOAD",
                "category": selected_category[0],
                "duration": "0:00",
                "views": "0",
                "video_path": selected_video_path[0],
            })
            app_state["video_category_filter"] = selected_category[0]
            cleanup_file_picker()
            show_snack("영상이 등록되었어요.")
            show_video_page()

        body = ft.Column(
            controls=[
                page_header("영상 올리기", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("영상 파일", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Text("MP4, MOV, M4V, WEBM 영상만 선택할 수 있어요.", size=11, color=SUBTEXT_COLOR),
                            ft.Container(height=8),
                            ft.Container(
                                width=content_width(),
                                height=52,
                                border_radius=RADIUS_MD,
                                border=ft.border.all(1.5, BORDER_COLOR),
                                bgcolor="#FAFAF8",
                                on_click=pick_video,
                                ink=True,
                                padding=ft.padding.symmetric(horizontal=16),
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.VIDEO_FILE_OUTLINED, size=18, color=MAIN_COLOR),
                                        ft.Text("영상 선택", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_500),
                                        ft.Container(expand=True),
                                        video_name_text,
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                        ],
                        spacing=4,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("카테고리", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            category_row,
                            ft.Container(height=12),
                            ft.Text("제목", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            title_field,
                            ft.Container(height=12),
                            ft.Text("설명", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            subtitle_field,
                        ],
                        spacing=0,
                    ),
                ),
                soft_button("영상 등록", MAIN_COLOR, "white", submit_video, width=content_width()),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_search_page():
        clear_transient_ui()
        if is_overlay_open("left"):
            app_state["selected_tab"] = 0
        elif is_overlay_open("right"):
            app_state["selected_tab"] = 4
        else:
            app_state["selected_tab"] = 2
        app_state["current_page"] = "search"

        def go_to_notice(e):
            open_notifications_page()

        search_logo_path = resolve_asset_file("findy_logo_horizontal.png")
        search_brand = (
            ft.Image(src=search_logo_path, width=164, height=36, fit=ft.ImageFit.CONTAIN)
            if search_logo_path
            else ft.Text("FINDY", size=30, weight=ft.FontWeight.BOLD, color=MAIN_COLOR)
        )

        header = ft.Container(
            width=content_width(),
            height=48,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=search_brand,
                    ),
                    ft.Container(
                        alignment=ft.Alignment(1, 0),
                        content=ft.IconButton(
                            icon=app_icon("NOTIFICATIONS_OUTLINED", "NOTIFICATIONS", "NOTIFICATION_ADD"),
                            icon_color=TEXT_COLOR,
                            icon_size=22,
                            tooltip="알림",
                            on_click=go_to_notice,
                        ),
                    ),
                ]
            ),
        )

        selected_main = app_state["selected_category"] or "헤어"
        app_state["selected_subcategory"] = None

        request_field = free_request_field(app_state["search_text"])
        request_field.width = 340
        request_field.min_lines = 9
        request_field.max_lines = 11

        async def search_click(e):
            entered_text = (request_field.value or "").strip()
            app_state["search_text"] = entered_text

            if not entered_text:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("원하는 스타일을 입력해주세요.", color="white"),
                    bgcolor="#B85C5C",
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
                page.snack_bar.open = True
                page.update()
                return

            app_state["recommendation_entry"] = None
            app_state["search_results_back_target"] = "search"
            await show_loading_page(
                {
                    "category": selected_main,
                    "free_request": entered_text,
                }
            )

        body = ft.Column(
            controls=[
                ft.Container(width=content_width(), content=header),
                ft.Container(height=8),
                ft.Container(
                    width=content_width(),
                    content=ft.Column(
                        controls=[
                            ft.Text("검색", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                            ft.Text(selected_main, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=3,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=10),
                request_field,
                ft.Container(height=12),
                soft_button("검색", MAIN_COLOR, "white", search_click, width=340),
                ft.Container(height=14),
                ft.Column(
                    controls=[
                        section_title("광고"),
                        ad_banner(),
                    ],
                    spacing=SPACE_MD,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=18),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    async def show_loading_page(user_data):
        map_text = ft.Text("🗺️", size=90)
        stickman = ft.Text("🧍", size=42)
        magnifier = ft.Text("🔍", size=34)

        status_text = ft.Text(
            "주변 아티스트를 탐색 중...",
            size=14,
            color=MAIN_COLOR,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        loading_card = ft.Container(
            width=content_width(),
            padding=30,
            bgcolor=CARD_COLOR,
            border_radius=RADIUS_XL,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color="#12000000",
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                controls=[
                    ft.Text(
                        "AI가 아티스트를 찾고 있어요",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "돋보기로 지도를 살펴보며 가장 잘 맞는 아티스트를 찾는 중...",
                        size=13,
                        color=SUBTEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[stickman, magnifier, map_text],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    ft.Container(height=12),
                    ft.ProgressRing(width=40, height=40, color=MAIN_COLOR, stroke_width=4),
                    status_text,
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        body = ft.Column(
            controls=[ft.Container(expand=True), loading_card, ft.Container(expand=True)],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        make_shell(body, app_state["selected_tab"])

        frames = [
            ("🧍", "🔍", "🗺️", "주변 아티스트를 탐색 중..."),
            ("🧍", "🔍", "🗺️", "스타일 취향을 분석 중..."),
            ("🧍", "🔍", "🗺️", "지역과 분위기를 매칭 중..."),
            ("🧍", "🔍", "🗺️", "추천 결과를 정리 중..."),
        ]

        for _ in range(2):
            for man, glass, map_icon, msg in frames:
                stickman.value = man
                magnifier.value = glass
                map_text.value = map_icon
                status_text.value = msg
                page.update()
                await asyncio.sleep(0.45)

        app_state["category_browse_mode"] = False
        app_state["search_results"] = build_recommended_artists(user_data)
        app_state["selected_category"] = user_data["category"]
        app_state["search_results_back_target"] = "search"
        show_search_results_page()

    def show_search_results_page():
        app_state["current_page"] = "search_results"
        app_state["selected_tab"] = app_state.get("selected_tab", 2)
        browse_mode = app_state.get("category_browse_mode", False)

        def distance_km(d):
            try:
                return float(str(d).replace("km", "").strip())
            except Exception:
                return 99.0

        _po = {"₩": 1, "₩₩": 2, "₩₩₩": 3}

        def apply_sort_filter(artists):
            sort_key = app_state.get("search_sort", "rating")
            if sort_key == "rating":
                artists = sorted(artists, key=lambda a: -float(a.get("rating", 0)))
            elif sort_key == "price_asc":
                artists = sorted(artists, key=lambda a: _po.get(a.get("price", "₩₩"), 2))
            elif sort_key == "price_desc":
                artists = sorted(artists, key=lambda a: -_po.get(a.get("price", "₩₩"), 2))
            elif sort_key == "distance":
                artists = sorted(artists, key=lambda a: distance_km(a.get("distance", "99km")))
            return artists

        def sort_chip(label, key):
            active = app_state.get("search_sort") == key
            def on_tap(e):
                app_state["search_sort"] = key
                show_search_results_page()
            return ft.GestureDetector(
                on_tap=on_tap,
                content=ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=7),
                    bgcolor=MAIN_COLOR if active else CHIP_BG,
                    border_radius=999,
                    content=ft.Text(label, size=12, color="white" if active else TEXT_COLOR, weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL),
                ),
            )

        raw_results = list(app_state.get("search_results") or [])
        is_artist_mode = not browse_mode or app_state.get("selected_subcategory") == "아티스트"
        filtered_results = apply_sort_filter(raw_results) if is_artist_mode else raw_results

        filter_bar = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[
                    sort_chip("평점순", "rating"),
                    sort_chip("거리순", "distance"),
                    sort_chip("가격낮은순", "price_asc"),
                    sort_chip("가격높은순", "price_desc"),
                ],
                spacing=6,
                scroll=ft.ScrollMode.HIDDEN,
            ),
        ) if is_artist_mode else ft.Container()

        result_count = ft.Container(
            width=content_width(),
            content=ft.Text(
                f"결과 {len(filtered_results)}개" if is_artist_mode else "",
                size=12,
                color=SUBTEXT_COLOR,
            ),
        ) if is_artist_mode else ft.Container()

        if browse_mode and app_state.get("selected_subcategory") == "통합검색":
            header_title = f"'{app_state.get('recommendation_entry', '')}' 검색 결과"
        else:
            header_title = f"{app_state.get('selected_subcategory', '')} 전체 보기" if browse_mode else "추천 아티스트"

        def go_back_search(e):
            back_target = app_state.get("search_results_back_target", "search")
            if back_target == "category":
                app_state["selected_tab"] = 0
                app_state["current_page"] = "category"
                show_category_page()
            elif back_target == "home":
                show_home_page()
            elif back_target == "snap_detail":
                show_snap_detail_page()
            else:
                show_search_page()

        cards = [
            page_header(header_title, on_back=go_back_search),
            ft.Container(height=4),
            filter_bar,
            result_count,
            ft.Container(height=4),
        ]

        if browse_mode and app_state.get("selected_subcategory") == "리뷰":
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=14),
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
                    on_click=lambda e: (
                        app_state.__setitem__("review_target", None),
                        app_state.__setitem__("current_page", "write_review"),
                        show_write_review_page(),
                    ),
                    ink=True,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADD_COMMENT_OUTLINED, size=18, color=MAIN_COLOR),
                            ft.Text("시술받은 아티스트로 리뷰 작성", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600, expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        if browse_mode and app_state.get("selected_subcategory") == "커뮤니티":
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=14),
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
                    on_click=lambda e: (
                        app_state.__setitem__("current_page", "write_community"),
                        show_write_community_page(),
                    ),
                    ink=True,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.EDIT_NOTE, size=19, color=MAIN_COLOR),
                            ft.Column(
                                controls=[
                                    ft.Text("커뮤니티 글쓰기", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                                    ft.Text("질문, 추천 요청, 전후 이야기를 남겨보세요.", size=11, color=ft.Colors.with_opacity(0.75, MAIN_COLOR)),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        if not filtered_results:
            empty_text = "조건에 맞는 아티스트가 없어요." if is_artist_mode else ("등록된 목록을 준비 중이에요." if browse_mode else "조건에 맞는 추천 결과를 준비 중이에요.")
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text(empty_text, size=13, color=SUBTEXT_COLOR),
                )
            )
        else:
            if browse_mode and app_state.get("selected_subcategory") != "아티스트":
                for item in filtered_results:
                    if item.get("type") == "artist" and item.get("artist_id"):
                        artist = find_artist_by_id(item.get("artist_id"))
                        cards.append(
                            browse_result_card(
                                item,
                                on_click=(lambda e, selected_artist=artist: open_detail(selected_artist, back_target="search")) if artist else None,
                            )
                        )
                    elif item.get("type") == "category":
                        cards.append(
                            browse_result_card(
                                item,
                                on_click=lambda e, category=item.get("title"): (
                                    app_state.__setitem__("selected_category", category),
                                    app_state.__setitem__("search_text", ""),
                                    show_search_page(),
                                ),
                            )
                        )
                    elif item.get("type") == "snap" and item.get("snap_id"):
                        snap_item = next((x for category in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"] for x in get_snap_feed_items("latest", category) if x["id"] == item.get("snap_id")), None)
                        cards.append(
                            browse_result_card(
                                item,
                                on_click=(lambda e, selected_snap=snap_item: open_snap_detail(selected_snap)) if snap_item else None,
                            )
                        )
                    else:
                        cards.append(browse_result_card(item))
            else:
                for artist in filtered_results:
                    cards.append(artist_result_card(artist, back_target="search"))

        cards.append(ft.Container(height=24))

        body = ft.Column(
            controls=cards,
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_saved_page():
        clear_transient_ui()
        app_state["current_page"] = "saved"
        app_state["selected_tab"] = 4
        saved_artists = [find_artist_by_id(aid) for aid in app_state["saved_ids"]]
        saved_artists = [a for a in saved_artists if a is not None]

        controls = [
            page_header("저장한 뷰티", on_back=go_back_page),
            ft.Text("찜해둔 아티스트를 모아볼 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
            ft.Container(height=12),
        ]

        if saved_artists:
            for artist in saved_artists:
                controls.append(compact_saved_card(artist))
        else:
            controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("아직 저장한 아티스트가 없어요.", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("검색 결과에서 저장 버튼을 눌러보세요.", size=13, color=SUBTEXT_COLOR),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        controls.append(ft.Container(height=24))

        body = ft.Column(
            controls=controls,
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_category_page():
        clear_transient_ui()
        app_state["selected_tab"] = 0
        app_state["current_page"] = "category"

        def toggle_category(main_category):
            if app_state.get("left_menu_expanded") == main_category:
                app_state["left_menu_expanded"] = None
            else:
                app_state["left_menu_expanded"] = main_category
            show_category_page()

        cards = []
        beauty_order = ["헤어", "네일아트", "포토", "웨딩", "반영구", "메이크업"]
        category_descriptions = {
            "헤어": "컷, 펌, 컬러와 스타일링",
            "네일아트": "젤, 케어, 디자인 네일",
            "포토": "프로필, 스냅, 콘셉트 촬영",
            "웨딩": "신부, 본식, 리허설 뷰티",
            "반영구": "눈썹, 아이라인, 입술 시술",
            "메이크업": "데일리, 화보, 신부 메이크업",
        }
        for main_category in beauty_order:
            is_expanded = app_state.get("left_menu_expanded") == main_category
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.only(left=16, right=14, top=15, bottom=15),
                    border_radius=26,
                    bgcolor="#FFFDFC" if not is_expanded else "#FFFAF6",
                    border=ft.border.all(1, ft.Colors.with_opacity(0.78, BORDER_COLOR)),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=18, color="#0E8B6B4F", offset=ft.Offset(0, 8)),
                    on_click=lambda e, category=main_category: toggle_category(category),
                    ink=True,
                    content=ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=42,
                                        height=42,
                                        border_radius=16,
                                        bgcolor="#F7F0E9",
                                        border=ft.border.all(1, "#EFE4D9"),
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(app_icon(left_overlay_icons.get(main_category, "CIRCLE")), size=20, color=MAIN_COLOR),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(main_category, size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                                            ft.Text(category_descriptions.get(main_category, "카테고리 둘러보기"), size=11, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=3,
                                    ),
                                ],
                                spacing=13,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                width=34,
                                height=34,
                                border_radius=999,
                                bgcolor="#F5EEE7",
                                border=ft.border.all(1, "#EFE4D9"),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(
                                    app_icon(
                                        "KEYBOARD_ARROW_DOWN" if is_expanded else "CHEVRON_RIGHT",
                                        "EXPAND_MORE",
                                        "ARROW_FORWARD_IOS",
                                    ),
                                    size=20,
                                    color=MAIN_COLOR,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
            if is_expanded:
                for sub_category in left_overlay_categories.get(main_category, []):
                    cards.append(
                        ft.Container(
                            width=content_width() - 28,
                            margin=ft.margin.only(left=14, top=4, bottom=2),
                            padding=ft.padding.symmetric(horizontal=14, vertical=11),
                            border_radius=16,
                            bgcolor="#FFFDFC",
                            border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                            on_click=lambda e, main=main_category, sub=sub_category: open_category_recommendations(main, sub),
                            ink=True,
                            content=ft.Row(
                                controls=[
                                    ft.Container(width=6, height=6, border_radius=999, bgcolor=MAIN_COLOR),
                                    ft.Text(sub_category, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                                    ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=SUBTEXT_COLOR),
                                ],
                                spacing=10,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        )
                    )

        body = ft.Column(
            controls=[
                tab_page_intro("카테고리", "원하는 항목을 빠르게 탐색해보세요."),
                ft.Container(height=16),
                *cards,
                ft.Container(height=24),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_my_page():
        clear_transient_ui()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my"

        body = ft.Column(
            controls=[
                tab_page_intro("내정보", "원하는 항목을 빠르게 탐색해보세요."),
                ft.Container(height=14),
                build_my_info_profile_card(),
                ft.Container(height=14),
                build_my_info_menu_section(),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def reservation_choice_chip(label, selected, on_click, width=None, height=56):
        return ft.Container(
            width=width,
            height=height,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            bgcolor=MAIN_COLOR if selected else ft.Colors.with_opacity(0.76, "#FFFFFF"),
            border_radius=18,
            border=ft.border.all(1, MAIN_COLOR if selected else BORDER_COLOR),
            on_click=on_click,
            ink=True,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(
                label,
                size=14,
                color="white" if selected else TEXT_COLOR,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        )

    def show_reservation_page():
        clear_transient_ui()
        form = get_reservation_form()
        artist = get_reservation_artist()
        if not artist:
            show_home_page()
            return

        app_state["current_page"] = "reservation"

        available_services = get_artist_services(artist)
        if available_services and form.get("service") not in available_services:
            form["service"] = available_services[0]

        note_field = ft.TextField(
            width=content_width(),
            value=form.get("note", ""),
            multiline=True,
            min_lines=4,
            max_lines=6,
            border_radius=4,
            bgcolor=CARD_COLOR,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=SPACE_LG,
            hint_text="요청사항이 있으면 적어주세요.",
            text_size=14,
            color=TEXT_COLOR,
        )

        def sync_note():
            form["note"] = note_field.value or ""

        def go_back(e):
            sync_note()
            show_detail_page()

        def choose_service(value):
            def handler(e):
                sync_note()
                form["service"] = value
                show_reservation_page()
            return handler

        def choose_date(value):
            def handler(e):
                sync_note()
                form["date"] = value
                form["time"] = None
                app_state["reservation_month_offset"] = month_offset
                show_reservation_page()
            return handler

        def change_month(delta):
            def handler(e):
                sync_note()
                next_offset = max(0, month_offset + delta)
                max_limit = get_artist_booking_limit_date(artist)
                candidate_month = (date.today().replace(day=1) + timedelta(days=32 * next_offset)).replace(day=1)
                if candidate_month > max_limit.replace(day=1):
                    show_snack("예약 가능한 마지막 달이에요.")
                    return
                app_state["reservation_month_offset"] = next_offset
                show_reservation_page()
            return handler

        def choose_time(value):
            def handler(e):
                sync_note()
                state = get_time_slot_state(artist, form.get("date"), value)
                if state == "booked":
                    show_snack("이미 마감된 시간이에요.", bgcolor="#B85C5C")
                    return
                if state == "past":
                    show_snack("지난 시간은 선택할 수 없어요.", bgcolor="#B85C5C")
                    return
                if state == "break":
                    show_snack("해당 시간은 휴식 시간이에요.", bgcolor="#B85C5C")
                    return
                if state in {"off_day", "blocked"}:
                    show_snack("해당 날짜는 예약이 열려 있지 않아요.", bgcolor="#B85C5C")
                    return
                form["time"] = value
                show_reservation_page()
            return handler

        def go_next(e):
            sync_note()
            if not form.get("service"):
                show_snack("시술 항목을 선택해주세요.", bgcolor="#B85C5C")
                return
            if not form.get("date") or not form.get("time"):
                show_snack("날짜와 시간을 선택해주세요.", bgcolor="#B85C5C")
                return
            if is_time_already_booked(artist["id"], form.get("date"), form.get("time")):
                show_snack("이미 마감된 시간이에요. 다른 시간을 선택해주세요.", bgcolor="#B85C5C")
                return
            show_reservation_confirm_page()

        selected_date = form.get("date")
        selected_time = form.get("time")
        selected_service = form.get("service")

        month_offset = max(0, app_state.get("reservation_month_offset", 0))
        month_anchor = (date.today().replace(day=1) + timedelta(days=32 * month_offset)).replace(day=1)
        year = month_anchor.year
        month = month_anchor.month
        month_name = f"{year}.{month:02d}"
        cal = calendar.Calendar(firstweekday=0)
        month_days = list(cal.monthdatescalendar(year, month))
        weekday_labels = ["월", "화", "수", "목", "금", "토", "일"]

        calendar_rows = []
        header_cells = []
        for label in weekday_labels:
            header_cells.append(
                ft.Container(
                    expand=True,
                    height=20,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(label, size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                )
            )
        calendar_rows.append(ft.Row(controls=header_cells, spacing=4))

        day_state_style = {
            "available": {"bg": "#FFFFFF", "border": BORDER_COLOR, "text": TEXT_COLOR, "opacity": 1.0},
            "off_day": {"bg": "#F3EEE8", "border": "#E4D7C8", "text": "#B09A83", "opacity": 1.0},
            "blocked": {"bg": "#F6F2ED", "border": "#E6DBCE", "text": "#AE9D8C", "opacity": 1.0},
            "past": {"bg": "#FBFAF8", "border": "#EEE6DB", "text": "#C7BAAC", "opacity": 0.9},
            "out_of_range": {"bg": "#FBFAF8", "border": "#EEE6DB", "text": "#C7BAAC", "opacity": 0.75},
        }

        for week in month_days:
            day_cells = []
            for d in week:
                in_month = d.month == month
                value = d.strftime("%Y-%m-%d")
                active = selected_date == value
                day_state = get_day_cell_state(artist, d) if in_month else "out_of_range"
                selectable = in_month and day_state == "available"

                if not in_month:
                    cell = ft.Container(
                        expand=True,
                        height=34,
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(str(d.day), size=12, color=ft.Colors.with_opacity(0.10, "#000000")),
                    )
                else:
                    style = day_state_style.get(day_state, day_state_style["available"])
                    badge_text = ""
                    if day_state == "off_day":
                        badge_text = "휴무"
                    elif day_state == "blocked":
                        badge_text = "마감"
                    bgcolor = MAIN_COLOR if active else style["bg"]
                    text_color = "white" if active else style["text"]
                    border_color = MAIN_COLOR if active else style["border"]
                    cell = ft.Container(
                        expand=True,
                        height=40,
                        border_radius=12,
                        bgcolor=bgcolor,
                        border=ft.border.all(1, border_color),
                        alignment=ft.Alignment(0, 0),
                        on_click=choose_date(value) if selectable else None,
                        ink=selectable,
                        opacity=1.0 if active else style["opacity"],
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    str(d.day),
                                    size=12,
                                    color=text_color,
                                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(badge_text, size=7.5, color=("white" if active else style["text"]), text_align=ft.TextAlign.CENTER) if badge_text else ft.Container(height=0),
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                day_cells.append(cell)

            calendar_rows.append(ft.Row(controls=day_cells, spacing=4))

        all_time_slots = generate_reservation_slots(artist)
        morning_slots = [value for value in all_time_slots if int(value.split(":")[0]) < 12]
        afternoon_slots = [value for value in all_time_slots if int(value.split(":")[0]) >= 12]

        grid_spacing = 4

        def build_time_card(value):
            active = selected_time == value
            state = get_time_slot_state(artist, selected_date, value) if selected_date else "need_date"
            disabled = state != "available"

            state_style = {
                "need_date": {"bg": "#FFFFFF", "border": ft.Colors.with_opacity(0.18, MAIN_COLOR), "text": SUBTEXT_COLOR},
                "available": {"bg": "#FFFFFF", "border": ft.Colors.with_opacity(0.22, MAIN_COLOR), "text": TEXT_COLOR},
                "booked": {"bg": "#E7DED4", "border": "#B4A292", "text": "#7D6D60"},
                "past": {"bg": "#FFFCF8", "border": "#E7DED5", "text": "#C6B9AD"},
                "break": {"bg": "#EFE7DE", "border": "#C9B59D", "text": "#827264"},
                "off_day": {"bg": "#EFE7DE", "border": "#C9B59D", "text": "#827264"},
                "blocked": {"bg": "#EFE7DE", "border": "#C9B59D", "text": "#827264"},
            }
            style = state_style.get(state, state_style["available"])

            return ft.Container(
                expand=True,
                height=36,
                border_radius=14,
                bgcolor=MAIN_COLOR if active else style["bg"],
                border=ft.border.all(1, MAIN_COLOR if active else style["border"]),
                alignment=ft.Alignment(0, 0),
                on_click=choose_time(value) if not disabled else None,
                ink=not disabled,
                opacity=1.0 if active else (0.82 if state == "booked" else 0.58 if state == "past" else 0.72 if disabled else 1.0),
                content=ft.Text(
                    value,
                    size=10.5,
                    color="white" if active else style["text"],
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
            )

        def chunked(values, size):
            return [values[idx:idx + size] for idx in range(0, len(values), size)]

        def build_time_grid(values):
            rows = []
            for row_values in chunked(values, 4):
                row_controls = [build_time_card(value) for value in row_values]
                while len(row_controls) < 4:
                    row_controls.append(ft.Container(expand=True, height=36))
                rows.append(ft.Row(controls=row_controls, spacing=grid_spacing, tight=True))
            return ft.Column(controls=rows, spacing=grid_spacing)

        service_controls = []
        for service in available_services or [form.get("service") or "기본 시술"]:
            service_controls.append(
                reservation_choice_chip(service, selected_service == service, choose_service(service), width=content_width(), height=54)
            )

        booking_limit = get_artist_booking_limit_date(artist)

        body = ft.Column(
            controls=[
                page_header("예약하기", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(artist["name"], size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(artist["job"], size=12, color=SUBTEXT_COLOR),
                            ft.Text("디자이너 운영 시간과 휴무일을 반영해서 예약 가능한 날짜만 보여드려요.", size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=SPACE_SM),
                            ft.Text("시술 선택", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("디자이너별로 제공하는 시술만 표시돼요.", size=12, color=SUBTEXT_COLOR),
                            ft.Column(controls=service_controls, spacing=SPACE_SM),
                            ft.Container(height=SPACE_MD),
                            ft.Text("날짜 선택", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(f"오늘부터 {booking_limit.strftime('%m/%d')}까지 예약 가능", size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=SPACE_SM),
                            ft.Row(
                                controls=[
                                    ft.IconButton(icon=app_icon("CHEVRON_LEFT", "ARROW_BACK_IOS_NEW", "ARROW_BACK"), icon_size=18, on_click=change_month(-1), disabled=month_offset <= 0),
                                    ft.Text(month_name, size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ft.IconButton(icon=app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"), icon_size=18, on_click=change_month(1), disabled=(month_anchor.replace(day=1) >= booking_limit.replace(day=1))),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(height=4),
                            ft.Column(controls=calendar_rows, spacing=4),
                            ft.Container(height=SPACE_SM),
                            ft.Row(
                                controls=[
                                    ft.Row(controls=[ft.Container(width=10, height=10, border_radius=999, bgcolor="#F3EEE8"), ft.Text("휴무", size=10, color=SUBTEXT_COLOR)], spacing=6),
                                    ft.Row(controls=[ft.Container(width=10, height=10, border_radius=999, bgcolor="#F6F2ED"), ft.Text("운영 마감", size=10, color=SUBTEXT_COLOR)], spacing=6),
                                ],
                                spacing=14,
                            ),
                            ft.Container(height=SPACE_MD),
                            ft.Text("시간 선택", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("예약된 시간은 회색, 지난 시간은 흐리게 비활성화돼요.", size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=SPACE_SM),
                            ft.Row(
                                controls=[
                                    ft.Row(controls=[ft.Container(width=10, height=10, border_radius=999, bgcolor="#E7DED4"), ft.Text("예약 마감", size=10, color=SUBTEXT_COLOR)], spacing=6),
                                    ft.Row(controls=[ft.Container(width=10, height=10, border_radius=999, bgcolor="#FFFCF8"), ft.Text("지난 시간", size=10, color=SUBTEXT_COLOR)], spacing=6),
                                ],
                                spacing=14,
                            ),
                            ft.Container(
                                width=content_width(),
                                padding=ft.padding.all(8),
                                bgcolor="#F8F4EF",
                                border_radius=18,
                                content=ft.Column(
                                    controls=[
                                        ft.Text("오전", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                        build_time_grid(morning_slots),
                                        ft.Container(height=4),
                                        ft.Text("오후", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                        build_time_grid(afternoon_slots),
                                    ],
                                    spacing=10,
                                ),
                            ),
                            ft.Container(height=SPACE_MD),
                            ft.Text("요청사항", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            note_field,
                            ft.Container(height=SPACE_SM),
                            ft.Container(
                                width=content_width(),
                                padding=ft.padding.symmetric(horizontal=14, vertical=14),
                                bgcolor="#F8F4EF",
                                border_radius=18,
                                content=ft.Column(
                                    controls=[
                                        ft.Text("예약 요약", size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                        ft.Text(f'시술: {selected_service or "선택 전"}', size=12, color=SUBTEXT_COLOR),
                                        ft.Text(f'날짜: {selected_date or "선택 전"}', size=12, color=SUBTEXT_COLOR),
                                        ft.Text(f'시간: {selected_time or "선택 전"}', size=12, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=4,
                                ),
                            ),
                            ft.Container(height=SPACE_MD),
                            soft_button("예약 확인", MAIN_COLOR, "white", go_next, width=field_width()),
                        ],
                        spacing=SPACE_SM,
                    ),
                ),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, None)

    def show_reservation_confirm_page():
        clear_transient_ui()

        form = get_reservation_form()
        artist = get_reservation_artist()
        if not artist:
            show_home_page()
            return

        app_state["current_page"] = "reservation_confirm"

        def go_back(e):
            show_reservation_page()

        def confirm_reservation(e):
            saved = save_reservation()
            if saved:
                show_reservation_complete_page()
            else:
                show_reservation_page()

        def confirm_row(label, value, value_color=None):
            return ft.Row(
                controls=[
                    ft.Text(label, size=13, color=SUBTEXT_COLOR, expand=True),
                    ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=value_color or TEXT_COLOR),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

        body = ft.Column(
            controls=[
                page_header("예약 확인", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    padding=22,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=14, color="#10000000", offset=ft.Offset(0, 4)),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=46,
                                        height=46,
                                        border_radius=RADIUS_MD,
                                        bgcolor=MAIN_COLOR_SOFT,
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(ft.Icons.PERSON_OUTLINED, size=22, color=MAIN_COLOR),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(artist["name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                            ft.Text(artist["job"], size=12, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=3,
                                        expand=True,
                                    ),
                                ],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(height=4),
                            ft.Container(height=1, bgcolor=BORDER_COLOR),
                            ft.Container(height=4),
                            confirm_row("시술", form.get("service", "기본 시술")),
                            ft.Container(height=1, bgcolor="#F5F3EF"),
                            confirm_row("날짜", form.get("date", "")),
                            ft.Container(height=1, bgcolor="#F5F3EF"),
                            confirm_row("시간", form.get("time", ""), value_color=MAIN_COLOR),
                            ft.Container(height=1, bgcolor="#F5F3EF"),
                            confirm_row("요청사항", form.get("note") or "없음"),
                            ft.Container(height=8),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                bgcolor="#FFF8F0",
                                border_radius=RADIUS_SM,
                                content=ft.Text("예약 후 내정보 > 예약내역에서 취소할 수 있어요.", size=11, color="#A07040"),
                            ),
                            ft.Container(height=8),
                            soft_button("예약 완료", MAIN_COLOR, "white", confirm_reservation, width=content_width() - 44),
                        ],
                        spacing=10,
                    ),
                ),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, None)

    def show_reservation_complete_page():
        clear_transient_ui()
        completed = app_state.get("last_completed_reservation")
        if not completed:
            show_home_page()
            return

        app_state["current_page"] = "reservation_complete"

        def go_home(e):
            show_home_page()

        def go_history(e):
            show_reservation_history_page()

        body = ft.Column(
            controls=[
                ft.Container(expand=True),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=20, color="#12000000", offset=ft.Offset(0, 6)),
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                width=72,
                                height=72,
                                border_radius=999,
                                bgcolor=MAIN_COLOR_SOFT,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.CHECK_ROUNDED, size=36, color=MAIN_COLOR),
                            ),
                            ft.Container(height=4),
                            ft.Text("예약이 완료되었어요", size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                            ft.Text("곧 아티스트에게 확인 안내가 전달돼요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=4),
                            ft.Container(
                                width=content_width() - SPACE_XL * 2,
                                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                                bgcolor="#FAFAF8",
                                border_radius=RADIUS_MD,
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text("아티스트", size=12, color=SUBTEXT_COLOR, expand=True),
                                                ft.Text(completed.get("artist_name", ""), size=12, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                                            ],
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Text("시술", size=12, color=SUBTEXT_COLOR, expand=True),
                                                ft.Text(completed.get("service", completed.get("category", "기본 시술")), size=12, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                                            ],
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Text("일시", size=12, color=SUBTEXT_COLOR, expand=True),
                                                ft.Text(f'{completed.get("date")}  {completed.get("time")}', size=12, weight=ft.FontWeight.W_600, color=MAIN_COLOR),
                                            ],
                                        ),
                                    ],
                                    spacing=10,
                                ),
                            ),
                            ft.Container(height=4),
                            soft_button("예약내역 보기", MAIN_COLOR, "white", go_history, width=content_width() - SPACE_XL * 2),
                            soft_button("홈으로", CHIP_BG, TEXT_COLOR, go_home, width=content_width() - SPACE_XL * 2),
                        ],
                        spacing=SPACE_MD,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        make_shell(body, None)

    def show_detail_page():
        clear_transient_ui()
        app_state["current_page"] = "detail"
        artist = app_state["detail_artist"]
        if not artist:
            show_home_page()
            return

        def go_back(e):
            target = app_state["detail_back_target"]
            if target == "saved":
                show_saved_page()
            elif target == "search":
                show_search_results_page()
            else:
                show_home_page()

        def save_click(e):
            toggle_saved(artist["id"])
            show_detail_page()

        def reserve_click(e):
            reset_reservation_form(artist)
            show_snack(f'{artist["name"]} 예약 화면으로 이동해요.')
            show_reservation_page()

        saved = is_saved(artist["id"])

        content = ft.Column(
            controls=[
                page_header("상세보기", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    height=200,
                    border_radius=RADIUS_XL,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Stack(
                        controls=[
                            black_image_box(content_width(), 200),
                            ft.Container(
                                left=16,
                                bottom=16,
                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                                border_radius=999,
                                content=ft.Text(artist["category"], size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                            ),
                            ft.Container(
                                right=16,
                                top=16,
                                content=ft.GestureDetector(
                                    on_tap=save_click,
                                    content=ft.Container(
                                        width=38,
                                        height=38,
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.88, "#FFFFFF"),
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(
                                            ft.Icons.BOOKMARK if saved else ft.Icons.BOOKMARK_BORDER,
                                            size=20,
                                            color=MAIN_COLOR if saved else SUBTEXT_COLOR,
                                        ),
                                    ),
                                ),
                            ),
                        ]
                    ),
                ),
                ft.Container(height=12),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=12, color="#12000000", offset=ft.Offset(0, 4)),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(artist["name"], size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                            ft.Text(artist["job"], size=13, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=3,
                                        expand=True,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(f"⭐ {artist['rating']}", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                            ft.Text(f"{artist['distance']}  {artist['price']}", size=11, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                            ft.Container(height=4),
                            ft.Container(height=1, bgcolor=BORDER_COLOR),
                            ft.Container(height=10),
                            ft.Text(artist["style"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(artist["intro"], size=13, color=SUBTEXT_COLOR),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=12, vertical=7),
                                        bgcolor=MAIN_COLOR_SOFT,
                                        border_radius=999,
                                        content=ft.Text(f"#{tag}", size=12, color=MAIN_COLOR, weight=ft.FontWeight.W_500),
                                    )
                                    for tag in artist["tags"]
                                ],
                                spacing=6,
                                wrap=True,
                            ),
                            ft.Container(height=10),
                            ft.Container(height=1, bgcolor=BORDER_COLOR),
                            ft.Container(height=10),
                            review_card("FINDY 사용자", artist["category"], artist["reason"]),
                        ],
                        spacing=SPACE_SM,
                    ),
                ),
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        ft.GestureDetector(
                            on_tap=save_click,
                            content=ft.Container(
                                width=56,
                                height=56,
                                border_radius=RADIUS_MD,
                                bgcolor="#FFFFFF",
                                border=ft.border.all(1, MAIN_COLOR if saved else BORDER_COLOR),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(
                                    ft.Icons.BOOKMARK if saved else ft.Icons.BOOKMARK_BORDER,
                                    size=22,
                                    color=MAIN_COLOR if saved else SUBTEXT_COLOR,
                                ),
                            ),
                        ),
                        ft.GestureDetector(
                            on_tap=reserve_click,
                            content=ft.Container(
                                expand=True,
                                height=56,
                                border_radius=RADIUS_MD,
                                bgcolor=MAIN_COLOR,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text("예약하기", size=15, color="white", weight=ft.FontWeight.BOLD),
                            ),
                        ),
                    ],
                    width=content_width(),
                    spacing=10,
                ),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        render_phone_frame(content, None)

    await start_opening_flow()

ft.app(target=main, assets_dir=ASSETS_DIR if os.path.isdir(ASSETS_DIR) else None)
