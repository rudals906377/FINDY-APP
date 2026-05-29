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
        return ft.Container(height=8, width=width or content_width())

    def page_header(title, on_back=None, width=None):
        return ft.Container(height=8, width=width or content_width())

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
            "review": "후기",
            "search": "검색",
            "search_results": "전체 보기",
            "snap_detail": "스냅",
        }
        return mapping.get(current_page, "")

    def section_title(title, subtitle=None, on_click=None):
        return ui_section_title(title, subtitle=subtitle, on_click=on_click, width=content_width())

    def soft_button(label, bgcolor, text_color, on_click, border=None, width=None):
        return ui_soft_button(label, bgcolor, text_color, on_click, border=border, width=width or field_width())

    def review_card(name, category, review):
        return ui_review_card(name, category, review, width=content_width())

    def browse_result_card(item):
        return ui_browse_result_card(item, width=content_width())

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
                width=168,
                fit="contain",
            )
        return brand_logo(show_slogan=False, compact=False)

    page.title = "FINDY276"
    regular_font = os.path.join(ASSETS_DIR, "Pretendard-Regular.ttf")
    bold_font = os.path.join(ASSETS_DIR, "Pretendard-Bold.ttf")
    if os.path.exists(regular_font) and os.path.exists(bold_font):
        page.fonts = {
            "Pretendard": "assets/Pretendard-Regular.ttf",
            "Pretendard-Bold": "assets/Pretendard-Bold.ttf",
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
        "last_completed_reservation": None,
        "reservation_month_offset": 0,
        "dismissed_upcoming_notice_id": None,
        "notification_read_at": None,
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

    def ad_banner():
        ad_texts = ["[ 광 고 ]", "[ 이 벤 트 ]", "[ 추 천 ]"]

        def refresh():
            ad_label.value = ad_texts[app_state["ad_index"]]
            page.update()

        def prev_ad(e):
            app_state["ad_index"] = (app_state["ad_index"] - 1) % len(ad_texts)
            refresh()

        def next_ad(e):
            app_state["ad_index"] = (app_state["ad_index"] + 1) % len(ad_texts)
            refresh()

        async def auto_slide():
            while True:
                await asyncio.sleep(3.0)
                if app_state["selected_tab"] == 0:
                    app_state["ad_index"] = (app_state["ad_index"] + 1) % len(ad_texts)
                    refresh()

        if not app_state["ad_task_started"]:
            app_state["ad_task_started"] = True
            page.run_task(auto_slide)

        ad_label = ft.Text(
            ad_texts[app_state["ad_index"]],
            size=28,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
        )

        return ft.Container(
            width=content_width(),
            height=160,
            bgcolor="#B07A48",
            border_radius=30,
            padding=SPACE_LG,
            border=ft.border.all(1, ft.Colors.with_opacity(0.30, "#FFFFFF")),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color="#22000000",
                offset=ft.Offset(0, 8),
            ),
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ad_label,
                    ),
                    ft.Container(
                        left=0,
                        top=0,
                        bottom=0,
                        alignment=ft.Alignment(-1, 0),
                        content=ft.IconButton(
                            icon=app_icon("CHEVRON_LEFT", "ARROW_BACK_IOS_NEW", "ARROW_BACK"),
                            icon_color="white",
                            on_click=prev_ad,
                        ),
                    ),
                    ft.Container(
                        right=0,
                        top=0,
                        bottom=0,
                        alignment=ft.Alignment(1, 0),
                        content=ft.IconButton(
                            icon=app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"),
                            icon_color="white",
                            on_click=next_ad,
                        ),
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
        return item.get("status") not in {"예약 취소", "시술 완료"}

    def get_reservation_status_meta(status):
        mapping = {
            "예약 완료": (MAIN_COLOR, "예약 확정"),
            "예약 취소": ("#B85C5C", "취소됨"),
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
                elif previous_page in {"my", "saved", "reservation_history"}:
                    app_state["selected_tab"] = 4
                render_current_page()
                return

        app_state["current_page"] = "home"
        app_state["selected_tab"] = 2
        show_home_page()

    def render_current_page():
        page_name = app_state.get("current_page", "home")
        if page_name == "snap":
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
        elif page_name == "review":
            show_review_page()
        elif page_name == "video":
            show_video_page()
        elif page_name == "snap_detail":
            show_snap_detail_page()
        elif page_name == "reservation":
            show_reservation_page()
        elif page_name == "reservation_confirm":
            show_reservation_confirm_page()
        elif page_name == "reservation_complete":
            show_reservation_complete_page()
        elif page_name == "notifications":
            show_notification_page()
        else:
            show_home_page()

    def go_category_page(e=None):
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 0
        app_state["current_page"] = "home"
        open_overlay("left")
        show_home_page()

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
        app_state["selected_tab"] = 4
        app_state["current_page"] = "home"
        open_overlay("right")
        show_home_page()

    def open_left_menu(e=None):
        go_category_page(e)

    def open_right_menu(e=None):
        go_my_page(e)

    def normalize_overlay_category_name(category_name):
        return "반영구시술" if category_name == "반영구" else category_name

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

        if sub_category == "후기":
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
                    "title": f"{artist['name']} 후기",
                    "subtitle": artist["job"],
                    "meta": f"⭐ {artist['rating']} · 방문자 후기",
                    "description": review_templates[idx % len(review_templates)],
                    "badge": "후기",
                })
            return result

        if sub_category == "커뮤니티":
            topics = ["추천 부탁드려요", "전후 사진 공유", "가격대 궁금해요", "첫 방문 후기"]
            return [
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

        return []

    def open_category_recommendations(main_category, sub_category):
        normalized_category = normalize_overlay_category_name(main_category)
        app_state["selected_category"] = normalized_category
        app_state["selected_subcategory"] = sub_category
        app_state["search_text"] = ""
        app_state["search_results"] = build_category_browse_items(main_category, sub_category)
        app_state["recommendation_entry"] = f"{main_category} > {sub_category}"
        app_state["category_browse_mode"] = True
        app_state["selected_tab"] = 2
        app_state["current_page"] = "search_results"
        close_overlays()
        show_search_results_page()

    def overlay_bottom_spacer():
        return ft.Container(height=NAV_BAR_HEIGHT + NAV_SAFE_GAP)

    def build_left_overlay():
        def toggle_main_category(main_category):
            if app_state.get("left_menu_expanded") == main_category:
                app_state["left_menu_expanded"] = None
            else:
                app_state["left_menu_expanded"] = main_category
            open_overlay("left")
            render_current_page()

        def build_section_header(label):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.only(top=10, bottom=8),
                content=ft.Text(
                    label,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_COLOR,
                ),
            )

        def build_main_row(main_category):
            is_expanded = app_state.get("left_menu_expanded") == main_category
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=14, vertical=14),
                bgcolor="#FFFFFF",
                border_radius=16,
                border=ft.border.all(1, BORDER_COLOR),
                on_click=lambda e, category=main_category: toggle_main_category(category),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Text(
                            main_category,
                            size=15,
                            weight=ft.FontWeight.W_600,
                            color=TEXT_COLOR,
                        ),
                        ft.Icon(
                            app_icon(
                                "KEYBOARD_ARROW_DOWN" if is_expanded else "CHEVRON_RIGHT",
                                "EXPAND_MORE",
                                "ARROW_FORWARD_IOS",
                            ),
                            size=20,
                            color=SUBTEXT_COLOR,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def build_sub_row(main_category, sub_category):
            return ft.Container(
                width=content_width() - 12,
                margin=ft.margin.only(left=12, top=6),
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                bgcolor="#FFFCF8",
                border_radius=14,
                border=ft.border.all(1, BORDER_COLOR),
                on_click=lambda e, main=main_category, sub=sub_category: open_category_recommendations(main, sub),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=7,
                            height=7,
                            border_radius=999,
                            bgcolor=MAIN_COLOR,
                        ),
                        ft.Text(
                            sub_category,
                            size=14,
                            color=TEXT_COLOR,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def board_action(label):
            show_snack(f"{label} 준비 중이에요.")

        def build_board_row(label):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=14, vertical=14),
                bgcolor="#FFFFFF",
                border_radius=16,
                border=ft.border.all(1, BORDER_COLOR),
                on_click=lambda e, value=label: board_action(value),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Text(
                            label,
                            size=15,
                            weight=ft.FontWeight.W_600,
                            color=TEXT_COLOR,
                        ),
                        ft.Icon(
                            app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"),
                            size=18,
                            color=SUBTEXT_COLOR,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        item_controls = [
            ft.Container(height=8),
            ft.Container(height=6),
            ft.Container(
                width=content_width(),
                height=48,
                padding=ft.padding.symmetric(horizontal=14),
                bgcolor="#FFFFFF",
                border_radius=14,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon("SEARCH"), size=18, color=SUBTEXT_COLOR),
                        ft.Text("검색", size=14, color=SUBTEXT_COLOR),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        ]

        beauty_order = ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
        for main_category in beauty_order:
            row_category = main_category
            lookup_key = main_category
            if main_category == "반영구":
                lookup_key = "반영구"
            item_controls.append(build_main_row(row_category))
            if app_state.get("left_menu_expanded") == row_category:
                for sub_category in left_overlay_categories.get(lookup_key, []):
                    item_controls.append(build_sub_row(row_category, sub_category))

        item_controls.extend([
            ft.Container(height=6),
            build_board_row("자유 게시판"),
            build_board_row("시술 후 일상 TIP"),
            build_board_row("개선 의견"),
            overlay_bottom_spacer(),
        ])

        return ft.Container(
            width=PHONE_WIDTH,
            height=PHONE_HEIGHT,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=PHONE_WIDTH,
                        height=PHONE_HEIGHT,
                        bgcolor=ft.Colors.with_opacity(0.18, "#000000"),
                    ),
                    ft.GestureDetector(
                        on_tap=lambda e: (close_overlays(), render_current_page()),
                        content=ft.Container(width=PHONE_WIDTH, height=PHONE_HEIGHT),
                    ),
                    ft.Container(
                        width=PHONE_WIDTH,
                        height=PHONE_HEIGHT,
                        alignment=ft.Alignment(-1, 0),
                        content=ft.Container(
                            width=PHONE_WIDTH,
                            height=PHONE_HEIGHT,
                            bgcolor="#FFFFFF",
                            padding=20,
                            content=ft.Column(
                                controls=item_controls,
                                spacing=4,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ),
                    ),
                ]
            ),
        )

    def build_right_overlay():
        return ft.Container(
            width=PHONE_WIDTH,
            height=PHONE_HEIGHT,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=PHONE_WIDTH,
                        height=PHONE_HEIGHT,
                        bgcolor=ft.Colors.with_opacity(0.18, "#000000"),
                    ),
                    ft.GestureDetector(
                        on_tap=lambda e: (close_overlays(), render_current_page()),
                        content=ft.Container(width=PHONE_WIDTH, height=PHONE_HEIGHT),
                    ),
                    ft.Container(
                        width=PHONE_WIDTH,
                        height=PHONE_HEIGHT,
                        alignment=ft.Alignment(1, 0),
                        content=ft.Container(
                            width=PHONE_WIDTH,
                            height=PHONE_HEIGHT,
                            bgcolor="#FFFFFF",
                            padding=24,
                            content=ft.Column(
                                controls=[
                                    ft.Container(height=8),
                                    ft.Container(height=12),
                                    build_my_info_profile_card(),
                                    ft.Container(height=14),
                                    build_my_info_menu_section(),
                                    overlay_bottom_spacer(),
                                ],
                                spacing=0,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ),
                    ),
                ]
            ),
        )

    def build_my_info_profile_card(width=None):
        width = width or layout_metrics()["content_width"]
        return ft.Container(
            width=width,
            padding=SPACE_LG,
            bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color="#0E000000",
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=1),
                                bgcolor=CHIP_BG,
                                border_radius=4,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=14),
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=64,
                                height=64,
                                border_radius=999,
                                bgcolor="#FFFCF8",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.PERSON, size=34, color=MAIN_COLOR),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("FINDY 회원", size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ft.Text("나에게 맞는 뷰티 기록을 관리해보세요.", size=10, color=SUBTEXT_COLOR),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                        ],
                        spacing=SPACE_MD,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                padding=ft.padding.symmetric(vertical=12),
                                bgcolor="#FFFFFF",
                                border_radius=RADIUS_MD,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    controls=[
                                        ft.Text("적립금", size=10, color=SUBTEXT_COLOR),
                                        ft.Text("12,500P", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ],
                                    spacing=3,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                expand=True,
                                padding=ft.padding.symmetric(vertical=12),
                                bgcolor="#FFFFFF",
                                border_radius=RADIUS_MD,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    controls=[
                                        ft.Text("쿠폰", size=10, color=SUBTEXT_COLOR),
                                        ft.Text("3장", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
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

    def build_my_info_menu_row(label, icon_name, on_click=None, enabled=True, badge_text=None):
        icon_color = MAIN_COLOR if enabled else ft.Colors.with_opacity(0.45, MAIN_COLOR)
        text_color = TEXT_COLOR if enabled else ft.Colors.with_opacity(0.55, TEXT_COLOR)
        arrow_color = SUBTEXT_COLOR if enabled else ft.Colors.with_opacity(0.45, SUBTEXT_COLOR)
        row_bgcolor = ft.Colors.TRANSPARENT if enabled else "#FFFFFF"

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
        trailing_controls.append(
            ft.Icon(
                app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS", "ARROW_FORWARD"),
                size=15,
                color=arrow_color,
            )
        )

        return ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=14,
            bgcolor=row_bgcolor,
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

    def build_my_info_menu_group(title, subtitle, items, width=None):
        width = width or layout_metrics()["content_width"]
        controls = [
            ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
            ft.Container(height=6),
        ]

        for item in items:
            controls.append(
                build_my_info_menu_row(
                    item["label"],
                    item["icon_name"],
                    item.get("action"),
                    enabled=item.get("enabled", True),
                    badge_text=item.get("badge_text"),
                )
            )

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

        body = ft.Column(
            controls=[
                page_header("후기"),
                ft.Container(height=10),
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
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state.get("selected_tab", 2))

    def show_placeholder_info_page(title, description):
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my"

        body = ft.Column(
            controls=[
                                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
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
        if item.get("status") == "예약 취소":
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

    def show_reservation_history_page():
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "reservation_history"

        history = list(reversed(app_state.get("reservation_history", [])))
        upcoming_items = [item for item in history if classify_history_item(item) == "upcoming"]
        past_items = [item for item in history if classify_history_item(item) == "past"]
        cancelled_items = [item for item in history if classify_history_item(item) == "cancelled"]

        controls = [
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

        meta_text = f'{item.get("date", "")}  {item.get("time", "")}'
        if kind == "past" and item.get("status") == "예약 완료":
            status_color = "#4F8A5B"
            status_label = "지난 예약"

        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
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
                ],
                spacing=8,
            ),
        )

    def build_my_info_menu_section(width=None):
        width = width or layout_metrics()["content_width"]
        implemented_items = [
            {
                "label": "예약내역",
                "icon_name": "CALENDAR_MONTH",
                "action": lambda e: (close_overlays(), show_reservation_history_page()),
                "enabled": True,
            },
            {
                "label": "저장한 뷰티",
                "icon_name": "BOOKMARK_BORDER",
                "action": lambda e: (close_overlays(), show_saved_page()),
                "enabled": True,
            },
        ]
        preparing_items = [
            {
                "label": "완료한 시술",
                "icon_name": "CHECK_CIRCLE_OUTLINE",
                "enabled": False,
                "badge_text": "준비 중",
            },
            {
                "label": "나의 뷰티 정보",
                "icon_name": "SPA_OUTLINED",
                "enabled": False,
                "badge_text": "준비 중",
            },
            {
                "label": "공지사항",
                "icon_name": "CAMPAIGN",
                "enabled": False,
                "badge_text": "준비 중",
            },
            {
                "label": "개선 의견",
                "icon_name": "LIGHTBULB_OUTLINE",
                "enabled": False,
                "badge_text": "준비 중",
            },
            {
                "label": "고객센터",
                "icon_name": "SUPPORT_AGENT",
                "enabled": False,
                "badge_text": "준비 중",
            },
            {
                "label": "문의내역",
                "icon_name": "CHAT_BUBBLE_OUTLINE",
                "enabled": False,
                "badge_text": "준비 중",
            },
        ]

        controls = [
            build_my_info_menu_group(
                "구현 완료",
                "지금 바로 사용할 수 있는 기능이에요.",
                implemented_items,
                width=width,
            ),
            ft.Container(
                width=width,
                margin=ft.margin.symmetric(vertical=8),
                border=ft.border.only(top=ft.BorderSide(1, BORDER_COLOR)),
            ),
            build_my_info_menu_group(
                "준비 중",
                "곧 연결될 기능은 비활성화되어 있어요.",
                preparing_items,
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
            bgcolor=ft.Colors.with_opacity(0.97, "#FFFFFF"),
            border_radius=ft.border_radius.only(top_left=22, top_right=22, bottom_left=0, bottom_right=0),
            border=ft.border.only(top=ft.BorderSide(0.6, ft.Colors.with_opacity(0.18, "#E7DED4"))),
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
        if current_page != last_page:
            if last_page and last_page != current_page and not (last_page == "login" and current_page == "home"):
                history = app_state.setdefault("page_history", [])
                if not history or history[-1] != last_page:
                    history.append(last_page)
            app_state["_last_rendered_page"] = current_page
        preserve_scroll_pages = {"reservation", "reservation_confirm", "reservation_complete"}
        full_height_pages = {"login"}
        nav_safe_bottom = (NAV_BAR_HEIGHT + NAV_SAFE_GAP) if nav_index is not None else 12
        nav_spacer = ft.Container(height=nav_safe_bottom)

        if current_page in preserve_scroll_pages:
            def remember_scroll(e):
                try:
                    app_state["reservation_scroll_offset"] = e.pixels
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

        phone_frame = ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            bgcolor="#FFFFFF",
            border_radius=30,
            clip_behavior=ft.ClipBehavior.NONE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#12000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[body_wrapper],
                spacing=0,
                expand=True,
            ),
        )

        stack_controls = [phone_frame]
        if is_overlay_open("left"):
            stack_controls.append(build_left_overlay())
        elif is_overlay_open("right"):
            stack_controls.append(build_right_overlay())
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

        if current_page in preserve_scroll_pages and scroll_view is not None:
            async def restore_scroll_position():
                await asyncio.sleep(0.01)
                try:
                    await scroll_view.scroll_to(
                        offset=app_state.get("reservation_scroll_offset", 0),
                        duration=0,
                    )
                except Exception:
                    try:
                        await scroll_view.scroll_to(
                            offset=app_state.get("reservation_scroll_offset", 0),
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
        card_width = 96
        image_width = 96
        image_height = 132
        emoji_size = 30
        title_size = 10
        desc_size = 8

        return ft.Container(
            width=card_width,
            padding=0,
            bgcolor=ft.Colors.with_opacity(0.88, "#FFFFFF"),
            border_radius=0,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10 if focused else 8,
                color="#0E000000",
                offset=ft.Offset(0, 2),
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        width=image_width,
                        height=image_height,
                        border_radius=0,
                        clip_behavior=ft.ClipBehavior.NONE,
                        bgcolor="#FFFDF9",
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    expand=True,
                                    bgcolor="#FFFDF9",
                                ),
                                ft.Container(
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(emoji, size=emoji_size),
                                ),
                                ft.Container(
                                    right=6,
                                    top=6,
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    bgcolor="#FFFFFF",
                                    border_radius=0,
                                    content=ft.Text("SNAP", size=6, color=TEXT_COLOR),
                                ),
                            ]
                        ),
                    ),
                    ft.Container(
                        padding=ft.padding.only(left=0, right=0, top=2, bottom=0),
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
                            spacing=1,
                        ),
                    ),
                ],
                spacing=4,
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
            height=196,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
                                border_radius=4,
                                bgcolor="#FFFDF9",
                                content=ft.Column(
                                    controls=[
                                        ft.Text("ARTIST", size=10, color=SUBTEXT_COLOR),
                                        ft.Text(
                                            artist["category"],
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXT_COLOR,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=4,
                                ),
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
                        bgcolor="#FFFDF9",
                        content=ft.Column(
                            controls=[
                                ft.Text("FINDY", size=10, color=SUBTEXT_COLOR),
                                ft.Text(artist["category"], size=10, color=TEXT_COLOR),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
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
                        bgcolor="#FFFDF9",
                        border_radius=RADIUS_MD,
                        content=ft.Row(
                            controls=[ft.Text("아티스트", size=12, color=SUBTEXT_COLOR)],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
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
            bgcolor="#FFFFFF",
            border_radius=30,
            clip_behavior=ft.ClipBehavior.NONE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#12000000",
                offset=ft.Offset(0, 6),
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

        def go_to_home(provider):
            def handler(e):
                show_snack(f"{provider} 로그인 중이에요.")
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
        accent = MAIN_COLOR if kind in {"upcoming", "confirmed"} else "#B85C5C"
        bg = "#FFFFFF" if kind != "cancelled" else "#FFF7F5"
        icon_name = "NOTIFICATIONS_ACTIVE" if kind == "upcoming" else "CHECK_CIRCLE" if kind == "confirmed" else "EVENT_BUSY"

        def open_notice_target(e=None):
            if item.get("item"):
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

        def go_to_category(category_name):
            def handler(e):
                app_state["selected_category"] = category_name
                app_state["selected_tab"] = 1
                show_search_page()
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

        header = ft.Container(
            width=content_width(),
            height=42,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("FINDY", size=28, weight=ft.FontWeight.BOLD, color=MAIN_COLOR),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(1, 0),
                        content=bell_button,
                    ),
                ]
            ),
        )

        search_bar = ft.TextField(
            width=content_width(),
            height=52,
            border_radius=20,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FFFFFF",
            hint_text="원하는 아티스트나 스타일 검색",
            hint_style=ft.TextStyle(color=SUBTEXT_COLOR, size=12),
            text_size=13,
            color=TEXT_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=ft.padding.symmetric(horizontal=18, vertical=14),
            prefix_icon=app_icon("SEARCH_ROUNDED", "SEARCH"),
        )

        category_box = build_category_box(go_to_category)

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
            search_bar,
            ft.Container(height=12),
            category_box,
        ])

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
                    section_title("후기", on_click=lambda e: show_review_page()),
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
        bar_count = mode
        return ft.Container(
            width=30,
            height=26,
            bgcolor=ft.Colors.with_opacity(0.88, "#FFFFFF") if active else ft.Colors.with_opacity(0.62, "#FFFFFF"),
            border_radius=14,
            border=ft.border.all(1.1, MAIN_COLOR if active else BORDER_COLOR),
            on_click=on_click,
            ink=True,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=4 if mode != 1 else 16,
                                height=10,
                                border_radius=6,
                                bgcolor=MAIN_COLOR if active else SUBTEXT_COLOR,
                            )
                            for _ in range(bar_count)
                        ],
                        spacing=2,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def snap_sort_chip(label, key):
        active = app_state.get("snap_sort_mode") == key

        def handle(e):
            app_state["snap_sort_mode"] = key
            show_snap_page()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=9, vertical=5),
            bgcolor=MAIN_COLOR if active else ft.Colors.with_opacity(0.72, "#FFFFFF"),
            border_radius=13,
            border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
            on_click=handle,
            ink=True,
            content=ft.Text(
                label,
                size=12,
                color="white" if active else TEXT_COLOR,
                weight=ft.FontWeight.W_600,
            ),
        )

    def snap_category_filter_chip(label):
        active = app_state.get("snap_filter", "헤어") == label

        def handle(e):
            app_state["snap_filter"] = label
            show_snap_page()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=9, vertical=5),
            bgcolor=MAIN_COLOR if active else ft.Colors.with_opacity(0.72, "#FFFFFF"),
            border_radius=13,
            border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
            on_click=handle,
            ink=True,
            content=ft.Text(
                label,
                size=12,
                color="white" if active else TEXT_COLOR,
                weight=ft.FontWeight.W_600,
            ),
        )

    def open_snap_detail(item):
        app_state["snap_detail_item"] = item
        show_snap_detail_page()

    def snap_photo_tile(item, width, height, layout_mode=1):
        view_style = "padded"
        is_full = False
        inner_margin = 0
        emoji_size = max(24, int(min(width, height) * 0.22))

        tile = ft.Container(
            width=width,
            height=height,
            border_radius=4,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=ft.Colors.with_opacity(0.28, item["accent"]),
            animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        expand=True,
                        margin=0,
                        border_radius=0,
                        bgcolor=item["accent"],
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment(0, 0),
                        margin=0,
                        content=ft.Text(item["emoji"], size=emoji_size),
                    ),
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

    def show_snap_page():
        clear_transient_ui()
        if is_overlay_open("left"):
            app_state["selected_tab"] = 0
        elif is_overlay_open("right"):
            app_state["selected_tab"] = 4
        else:
            app_state["selected_tab"] = 1
        app_state["current_page"] = "snap"

        def choose_layout(mode):
            def handler(e):
                app_state["snap_layout_mode"] = mode
                show_snap_page()
            return handler

        sort_row = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        bgcolor=ft.Colors.with_opacity(0.45, "#FFFFFF"),
                        border_radius=18,
                        content=ft.Row(
                            controls=[
                                snap_layout_selector_button(1, app_state.get("snap_layout_mode", 3), choose_layout(1)),
                                snap_layout_selector_button(3, app_state.get("snap_layout_mode", 3), choose_layout(3)),
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ),
                    ft.Container(width=8, height=1),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        bgcolor=ft.Colors.with_opacity(0.45, "#FFFFFF"),
                        border_radius=18,
                        content=ft.Row(
                            controls=[
                                snap_sort_chip("인기순", "popular"),
                                snap_sort_chip("최신순", "latest"),
                                snap_sort_chip("추천순", "recommended"),
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                spacing=4,
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
                spacing=10,
                wrap=True,
            ),
        )

        body = ft.Column(
            controls=[
                page_header("스냅"),
                ft.Container(height=8),
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

    def snap_detail_stat(label, value, icon_name):
        return ft.Container(
            expand=True,
            padding=ft.padding.symmetric(vertical=10),
            bgcolor=ft.Colors.with_opacity(0.68, "#FFFFFF"),
            border_radius=RADIUS_MD,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Icon(app_icon(icon_name), size=18, color=MAIN_COLOR),
                    ft.Text(str(value), size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ft.Text(label, size=10, color=SUBTEXT_COLOR),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def snap_detail_thumbnail(item, index):
        return ft.Container(
            width=100,
            height=100,
            border_radius=4,
            bgcolor=item["accent"],
            clip_behavior=ft.ClipBehavior.NONE,
            content=ft.Stack(
                controls=[
                    ft.Container(expand=True, bgcolor=item["accent"]),
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(item["emoji"], size=26),
                    ),
                    ft.Container(
                        right=8,
                        bottom=8,
                        padding=ft.padding.symmetric(horizontal=7, vertical=3),
                        bgcolor="#FFFFFF",
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
                    bgcolor=ft.Colors.with_opacity(0.28, item["accent"]),
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                expand=True,
                                margin=0 if False else 18,
                                border_radius=0 if False else 22,
                                bgcolor=item["accent"],
                            ),
                            ft.Container(
                                expand=True,
                                margin=0 if False else 18,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(item["emoji"], size=96 if False else 84),
                            ),
                            ft.Container(
                                left=14,
                                top=14,
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor="#FFFFFF",
                                border_radius=4,
                                content=ft.Text("대표 이미지", size=10, color=TEXT_COLOR),
                            ),
                            ft.Container(
                                right=14,
                                bottom=14,
                                padding=ft.padding.symmetric(horizontal=8, vertical=1),
                                bgcolor="#FFFFFF",
                                border_radius=4,
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
                            ft.Text("감성 스냅 예시 화면 · 빈칸 대신 플레이스홀더로 구성", size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=10),
                            ft.Row(
                                controls=[
                                    snap_detail_stat("조회", item["views"], "REMOVE_RED_EYE_OUTLINED"),
                                    snap_detail_stat("좋아요", item["likes"], "FAVORITE_BORDER"),
                                    snap_detail_stat("저장", item["saves"], "BOOKMARK_BORDER"),
                                ],
                                spacing=8,
                            ),
                            ft.Container(height=14),
                            ft.Text("설명", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(
                                "청순하고 부드러운 무드의 스냅 예시예요. 실제 사진 대신 빈 이미지 칸 느낌으로 구성했고, 나중에 네가 직접 사진만 바꾸면 바로 사용할 수 있게 만들어뒀어.",
                                size=13,
                                color=SUBTEXT_COLOR,
                            ),
                            ft.Container(height=12),
                            ft.Text("예시 이미지 모음", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
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
                        ],
                        spacing=0,
                    ),
                ),
                ft.Container(height=16),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_video_page():
        clear_transient_ui()
        if is_overlay_open("left"):
            app_state["selected_tab"] = 0
        elif is_overlay_open("right"):
            app_state["selected_tab"] = 4
        else:
            app_state["selected_tab"] = 3
        app_state["current_page"] = "video"

        def video_card(title, subtitle, badge):
            return ft.Container(
                width=content_width(),
                height=186,
                border_radius=RADIUS_XL,
                bgcolor="#FFFDF9",
                padding=SPACE_LG,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=16,
                    color="#10000000",
                    offset=ft.Offset(0, 6),
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
                            content=ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                border_radius=999,
                                bgcolor=ft.Colors.with_opacity(0.86, "#FFFFFF"),
                                content=ft.Text(badge, size=10, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ),
                        ),
                        ft.Container(
                            left=0,
                            right=0,
                            bottom=0,
                            content=ft.Column(
                                controls=[
                                    ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ft.Text(subtitle, size=12, color=SUBTEXT_COLOR),
                                ],
                                spacing=4,
                            ),
                        ),
                    ]
                ),
            )

        body = ft.Column(
            controls=[
                page_header("비디오"),
                ft.Container(height=2),
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                bgcolor=CHIP_BG,
                                border_radius=999,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=12),
                video_card("오늘의 스타일 숏츠", "짧고 빠르게 분위기 참고하기", "SHORTS"),
                video_card("인기 릴스 모아보기", "사람들이 많이 본 스타일 영상", "REELS"),
                video_card("트렌드 비디오", "요즘 많이 저장하는 룩 영상", "TREND"),
                ft.Container(height=18),
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
            page.snack_bar = ft.SnackBar(ft.Text("알림 기능은 다음 단계에서 연결할게."))
            page.snack_bar.open = True
            page.update()

        header = ft.Container(
            width=content_width(),
            height=48,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("FINDY", size=30, weight=ft.FontWeight.BOLD, color=MAIN_COLOR),
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
        current_subcategories = subcategories.get(selected_main, [])

        def choose_sub(sub):
            def handler(e):
                app_state["selected_subcategory"] = sub
                show_search_page()
            return handler

        request_field = subcategory_request_field(
            selected_main,
            app_state.get("selected_subcategory"),
            app_state["search_text"],
        )
        request_field.width = 340
        request_field.min_lines = 9
        request_field.max_lines = 11

        async def search_click(e):
            selected_sub = app_state.get("selected_subcategory")
            entered_text = (request_field.value or "").strip()
            app_state["search_text"] = entered_text

            if not selected_sub:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("카테고리를 선택해주세요.", color="white"),
                    bgcolor="#B85C5C",
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
                page.snack_bar.open = True
                page.update()
                return

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
            await show_loading_page(
                {
                    "category": selected_main,
                    "subcategory": selected_sub,
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
                ft.Column(
                    width=content_width(),
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    expand=True,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                                    bgcolor=MAIN_COLOR if sub == app_state.get("selected_subcategory") else CHIP_BG,
                                    border_radius=4,
                                    on_click=choose_sub(sub),
                                    ink=True,
                                    content=ft.Text(
                                        sub,
                                        size=12,
                                        color="white" if sub == app_state.get("selected_subcategory") else TEXT_COLOR,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                )
                                for sub in current_subcategories[i:i+2]
                            ],
                            spacing=2,
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                        for i in range(0, len(current_subcategories), 2)
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
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
        show_search_results_page()

    def show_search_results_page():
        app_state["current_page"] = "search_results"
        app_state["selected_tab"] = app_state.get("selected_tab", 2)
        selected_category_label = app_state.get("selected_category") or "헤어"
        entry_label = app_state.get("recommendation_entry")
        browse_mode = app_state.get("category_browse_mode", False)

        if browse_mode:
            selected_sub = app_state.get("selected_subcategory") or "목록"
            subtitle = None
            header_title = f"{selected_sub} 전체 보기"
        else:
            subtitle = None
            header_title = "추천 아티스트"

        cards = [
            ft.Container(height=12),
        ]

        if not app_state.get("search_results"):
            empty_text = "등록된 목록을 준비 중이에요." if browse_mode else "조건에 맞는 추천 결과를 준비 중이에요."
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
            if browse_mode and (app_state.get("selected_subcategory") == "아티스트"):
                for artist in app_state["search_results"]:
                    cards.append(artist_result_card(artist, back_target="search"))
            elif browse_mode:
                for item in app_state["search_results"]:
                    cards.append(browse_result_card(item))
            else:
                for artist in app_state["search_results"]:
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
        app_state["selected_tab"] = 0
        saved_artists = [find_artist_by_id(aid) for aid in app_state["saved_ids"]]
        saved_artists = [a for a in saved_artists if a is not None]

        controls = [
            section_title("저장", "찜해둔 아티스트를 모아볼 수 있어요."),
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

    def show_my_page():
        clear_transient_ui()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my"

        def go_back(e):
            show_home_page()

        body = ft.Column(
            controls=[
                page_header("내정보"),
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

        body = ft.Column(
            controls=[
                page_header("예약 확인", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    padding=22,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("아래 내용으로 예약을 진행할까요?", size=13, color=SUBTEXT_COLOR),
                            ft.Container(height=8),
                            ft.Text(artist["name"], size=17, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(artist["job"], size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=10),
                            ft.Text(f'시술: {form.get("service", "기본 시술")}', size=14, color=TEXT_COLOR),
                            ft.Text(f'날짜: {form.get("date")}', size=14, color=TEXT_COLOR),
                            ft.Text(f'시간: {form.get("time")}', size=14, color=TEXT_COLOR),
                            ft.Text('예약 완료 후 내정보 > 예약내역에서 취소할 수 있어요.', size=12, color=SUBTEXT_COLOR),
                            ft.Text(
                                f'요청사항: {form.get("note") or "없음"}',
                                size=13,
                                color=SUBTEXT_COLOR,
                            ),
                            ft.Container(height=10),
                            soft_button("예약 완료", MAIN_COLOR, "white", confirm_reservation, width=content_width()),
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
                ft.Container(height=20),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                    border_radius=30,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("예약이 완료되었어요", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                f'{completed.get("artist_name")} · {completed.get("service", completed.get("category", "기본 시술"))}',
                                size=13,
                                color=SUBTEXT_COLOR,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                f'{completed.get("date")} · {completed.get("time")}',
                                size=13,
                                color=SUBTEXT_COLOR,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=8),
                            soft_button("예약내역 보기", MAIN_COLOR, "white", go_history, width=field_width()),
                            soft_button("홈으로", CHIP_BG, TEXT_COLOR, go_home, width=field_width()),
                        ],
                        spacing=SPACE_MD,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
                page_header("내정보"),
                page_header("상세보기"),
                ft.Container(
                    width=content_width(),
                    height=220,
                    bgcolor=ft.Colors.with_opacity(0.60, "#FFFFFF"),
                    border_radius=32,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("FINDY", size=15, weight=ft.FontWeight.BOLD, color=SUBTEXT_COLOR),
                            ft.Text(artist["category"], size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("대표 이미지 자리", size=12, color=SUBTEXT_COLOR),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                ),
                ft.Container(height=16),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=30,
                    border=ft.border.all(1, BORDER_COLOR),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=12,
                        color="#12000000",
                        offset=ft.Offset(0, 4),
                    ),
                    content=ft.Column(
                        controls=[
                            ft.Text(artist["name"], size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(artist["job"], size=13, color=SUBTEXT_COLOR),
                            ft.Row(
                                controls=[
                                    ft.Text(f"⭐ {artist['rating']}", size=13, color=TEXT_COLOR),
                                    ft.Text(f"· {artist['distance']}", size=13, color=SUBTEXT_COLOR),
                                    ft.Text(f"· {artist['price']}", size=13, color=SUBTEXT_COLOR),
                                ],
                                spacing=10,
                            ),
                            ft.Container(height=4),
                            ft.Text(artist["style"], size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text(artist["intro"], size=13, color=SUBTEXT_COLOR),
                            ft.Container(height=8),
                            ft.Text("스타일 태그", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                        bgcolor=CHIP_BG,
                                        border_radius=4,
                                        content=ft.Text(f"#{tag}", size=12, color=TEXT_COLOR),
                                    )
                                    for tag in artist["tags"]
                                ],
                                spacing=2,
                                wrap=True,
                            ),
                            ft.Container(height=10),
                            review_card("LOOQ 사용자", artist["category"], artist["reason"]),
                            ft.Container(height=10),
                            ft.Row(
                                controls=[
                                    soft_button("저장됨" if saved else "저장", CHIP_BG, TEXT_COLOR, save_click, width=150),
                                    soft_button("예약하기", MAIN_COLOR, "white", reserve_click, width=150),
                                ],
                                spacing=SPACE_MD,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=SPACE_MD,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        render_phone_frame(content, None)

    await start_opening_flow()

ft.app(target=main, assets_dir=ASSETS_DIR if os.path.isdir(ASSETS_DIR) else None)