import asyncio
import json
import math
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
    LOGO_COLOR,
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
APP_RUNTIME_MODE = os.environ.get("FINDY_APP_MODE", "combined").strip().lower()
if APP_RUNTIME_MODE not in {"combined", "customer", "artist"}:
    APP_RUNTIME_MODE = "combined"

async def main(page: ft.Page):

    def is_customer_runtime():
        return APP_RUNTIME_MODE == "customer"

    def is_artist_runtime():
        return APP_RUNTIME_MODE == "artist"

    def is_combined_runtime():
        return APP_RUNTIME_MODE == "combined"

    def safe_go_back(e=None):
        try:
            go_back_page(e)
        except Exception:
            try:
                if is_artist_runtime():
                    show_artist_main_page()
                else:
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
            "artist_trend_analysis": "트렌드 분석",
            "artist_profile_preview": "아티스트 프로필",
            "artist_profile_post": "게시물",
            "artist_portfolio_add": "포트폴리오 추가",
            "artist_price_menu": "가격 메뉴",
            "snap_detail": "스냅",
            "support": "고객센터",
            "inquiry": "문의내역",
            "customer_messages": "메시지",
            "artist_messages": "메시지",
            "message_artist_search": "아티스트 검색",
            "write_artist_message": "메시지 작성",
            "message_detail": "메시지 상세",
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

    def is_artist_manage_mode():
        user = app_state.get("current_user") or {}
        return user.get("role") == "artist"

    def review_item_name(item, fallback="고객"):
        if isinstance(item, dict):
            return item.get("name") or fallback
        if isinstance(item, (tuple, list)) and len(item) > 0:
            return item[0] or fallback
        return fallback

    def review_item_category(item, fallback="헤어"):
        if isinstance(item, dict):
            return item.get("category") or fallback
        if isinstance(item, (tuple, list)) and len(item) > 1:
            return item[1] or fallback
        return fallback

    def review_item_body(item, fallback=""):
        if isinstance(item, dict):
            return item.get("review") or item.get("body") or fallback
        if isinstance(item, (tuple, list)) and len(item) > 2:
            return item[2] or fallback
        return fallback

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

    def login_logo_visual(width=156):
        path = resolve_asset_file(LOGIN_BRAND_IMAGE)
        if path:
            return ft.Image(
                src=path,
                width=width,
                fit="contain",
            )
        return brand_logo(show_slogan=False, compact=False)

    page.title = {
        "customer": "FINDY 고객",
        "artist": "FINDY 아티스트",
    }.get(APP_RUNTIME_MODE, "FINDY")
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
        "artist_trend_period": "주별",
        "artist_trend_category": "헤어",
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
        "video_liked_keys": set(),
        "video_saved_keys": set(),
        "video_category_filter": "전체",
        "video_detail_item": None,
        "my_content_type": "리뷰",
        "saved_content_type": "아티스트",
        "content_detail_item": None,
        "artist_available_slots": ["11:00", "12:30", "15:00", "17:30", "19:00"],
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
        "message_threads": [],
        "active_message_thread_id": None,
        "message_draft": {
            "artist_id": None,
            "category": "스타일 상담",
            "content": "",
        },
        "message_artist_query": "",
        "message_reply_draft": "",
        "message_back_target": None,
        "completion_feedback": None,
        "artist_approval_status": "approved",
        "artist_notifications": [],
        "reported_content_ids": set(),
        "hidden_content_ids": set(),
        "my_info_expanded_sections": set(),
        "artist_profile_public": True,
        "artist_consulting_enabled": True,
        "artist_profile": {
            "name": "OO 아티스트",
            "field": "헤어 디자이너",
            "category": "헤어",
            "region": "강남",
            "shop": "OO 샵",
            "mood": "감성 · 트렌디 · 내추럴",
            "career": "8년차 헤어 디자이너로 얼굴형과 분위기에 맞는 스타일을 제안해요.",
            "instagram": "@findy_sua",
            "hours": "화-토 11:00 - 20:00",
            "public": True,
        },
        "artist_portfolio_items": [
            {
                "id": "portfolio_1",
                "menu_id": "menu_1",
                "title": "레이어드컷 + 볼륨펌",
                "category": "헤어",
                "style": "감성",
                "price": "12만원대",
                "description": "자연스럽게 흐르는 층과 부드러운 볼륨을 살린 스타일",
                "public": True,
                "representative": True,
            },
            {
                "id": "portfolio_2",
                "menu_id": "menu_2",
                "title": "애쉬그레이 컬러",
                "category": "헤어",
                "style": "트렌디",
                "price": "18만원대",
                "description": "차분하지만 선명한 무드가 살아나는 컬러",
                "public": True,
                "representative": False,
            },
        ],
        "artist_price_menu_items": [
            {
                "id": "menu_1",
                "name": "레이어드컷 + 볼륨펌",
                "category": "헤어",
                "duration": "120분",
                "price": "12만원대",
                "description": "얼굴형과 길이감에 맞춰 레이어드와 볼륨감을 함께 제안해요.",
                "available": True,
            },
            {
                "id": "menu_2",
                "name": "애쉬그레이 컬러",
                "category": "헤어",
                "duration": "150분",
                "price": "18만원대",
                "description": "차분하지만 선명한 무드가 살아나는 컬러 시술이에요.",
                "available": True,
            },
        ],
        "page_history": [],
        "_last_rendered_page": None,
    }

    ARTIST_PROFILE_DEFAULTS = {
        "name": "OO 아티스트",
        "field": "헤어 디자이너",
        "category": "헤어",
        "region": "강남",
        "shop": "OO 샵",
        "mood": "감성 · 트렌디 · 내추럴",
        "career": "8년차 헤어 디자이너로 얼굴형과 분위기에 맞는 스타일을 제안해요.",
        "instagram": "@findy_sua",
        "hours": "화-토 11:00 - 20:00",
        "public": True,
    }

    ARTIST_PRICE_MENU_DEFAULTS = {
        "id": "",
        "name": "시술명",
        "category": "헤어",
        "duration": "상담 후 안내",
        "price": "상담 후 안내",
        "description": "아직 상세 설명이 없어요.",
        "available": True,
    }

    ARTIST_PORTFOLIO_DEFAULTS = {
        "id": "",
        "menu_id": None,
        "title": "시술명",
        "category": "헤어",
        "style": "감성",
        "duration": "",
        "price": "상담 후 안내",
        "description": "사진과 설명을 추가해 대표 스타일을 완성해보세요.",
        "public": True,
        "representative": False,
        "has_photo": False,
    }

    def _clone_artist_default(value):
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return dict(value)
        return value

    def ensure_artist_data():
        profile = app_state.setdefault("artist_profile", {})
        for key, value in ARTIST_PROFILE_DEFAULTS.items():
            profile.setdefault(key, _clone_artist_default(value))
        if "artist_profile_public" in app_state:
            profile["public"] = bool(app_state["artist_profile_public"])
        else:
            app_state["artist_profile_public"] = bool(profile.get("public", True))

        price_menus = app_state.setdefault("artist_price_menu_items", [])
        for index, menu in enumerate(price_menus, start=1):
            for key, value in ARTIST_PRICE_MENU_DEFAULTS.items():
                menu.setdefault(key, _clone_artist_default(value))
            if not menu.get("id"):
                menu["id"] = f"menu_{index}"

        menu_by_id = {menu.get("id"): menu for menu in price_menus if menu.get("id")}
        menu_by_name = {menu.get("name"): menu for menu in price_menus if menu.get("name")}

        portfolio_items = app_state.setdefault("artist_portfolio_items", [])
        for index, item in enumerate(portfolio_items, start=1):
            for key, value in ARTIST_PORTFOLIO_DEFAULTS.items():
                item.setdefault(key, _clone_artist_default(value))
            if not item.get("id"):
                item["id"] = f"portfolio_{index}"
            if not item.get("menu_id"):
                matched_menu = menu_by_name.get(item.get("title"))
                if matched_menu:
                    item["menu_id"] = matched_menu.get("id")

            linked_menu = menu_by_id.get(item.get("menu_id"))
            if linked_menu:
                item["title"] = linked_menu.get("name", item.get("title", "시술명"))
                item["category"] = linked_menu.get("category", item.get("category", "헤어"))
                item["duration"] = linked_menu.get("duration", item.get("duration", ""))
                item["price"] = linked_menu.get("price", item.get("price", "상담 후 안내"))
                item["description"] = item.get("description") or linked_menu.get("description", ARTIST_PORTFOLIO_DEFAULTS["description"])

        return profile

    def get_artist_profile():
        return ensure_artist_data()

    def get_artist_price_menus(*, available_only=False):
        ensure_artist_data()
        items = app_state.setdefault("artist_price_menu_items", [])
        if available_only:
            return [item for item in items if item.get("available", True)]
        return items

    def get_artist_portfolio_items():
        ensure_artist_data()
        return app_state.setdefault("artist_portfolio_items", [])

    def get_artist_price_menu_by_id(menu_id):
        if not menu_id:
            return None
        return next((menu for menu in get_artist_price_menus() if menu.get("id") == menu_id), None)

    ensure_artist_data()

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
        path = resolve_asset_file("app_logo/app_findy_logo_mark.png")
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
        image_name = "app_logo/app_findy_logo_vertical.png" if show_slogan else "app_logo/app_findy_logo_horizontal.png"
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

    def open_completion_feedback(title, message, next_label, next_page, selected_tab=None, icon_name="CHECK_CIRCLE"):
        app_state["completion_feedback"] = {
            "title": title,
            "message": message,
            "next_label": next_label,
            "next_page": next_page,
            "selected_tab": selected_tab,
            "icon": icon_name,
        }
        if selected_tab is not None:
            app_state["selected_tab"] = selected_tab
        app_state["current_page"] = "completion_feedback"
        render_current_page()

    def record_artist_notification(kind, title, body, target_page=None):
        notifications = app_state.setdefault("artist_notifications", [])
        notifications.insert(
            0,
            {
                "id": f"artist:{kind}:{datetime.now().timestamp()}",
                "kind": kind,
                "title": title,
                "body": body,
                "timestamp": datetime.now(),
                "target_page": target_page,
            },
        )

    def seed_message_threads():
        threads = app_state.setdefault("message_threads", [])
        if threads:
            return threads

        profile = get_artist_profile()
        threads.append(
            {
                "id": "msg_seed_1",
                "artist_id": "artist_self",
                "artist_name": profile.get("name", "OO 아티스트"),
                "artist_category": profile.get("category", "헤어"),
                "customer_name": "김수아",
                "category": "스타일 상담",
                "status": "답장 필요",
                "updated_at": "오늘 10:20",
                "messages": [
                    {
                        "sender": "customer",
                        "text": "안녕하세요. 레이어드컷 상담 가능할까요?",
                        "time": "오늘 10:20",
                    }
                ],
            }
        )
        return threads

    def current_message_threads():
        return seed_message_threads()

    def find_message_thread(thread_id):
        return next((thread for thread in current_message_threads() if thread.get("id") == thread_id), None)

    def find_message_thread_by_artist(artist_id):
        if not artist_id:
            return None
        return next(
            (thread for thread in current_message_threads() if thread.get("artist_id") == artist_id),
            None,
        )

    def open_message_thread(thread_id, back_target=None):
        app_state["active_message_thread_id"] = thread_id
        app_state["message_reply_draft"] = ""
        app_state["message_back_target"] = back_target or app_state.get("current_page")
        app_state["current_page"] = "message_detail"
        render_current_page()

    def start_customer_chat_with_artist(artist, back_target="message_artist_search"):
        if is_artist_runtime() or is_artist_manage_mode():
            show_snack("아티스트 모드에서는 고객 메시지를 먼저 작성할 수 없어요.", bgcolor="#B85C5C")
            return
        existing_thread = find_message_thread_by_artist(artist.get("id"))
        if existing_thread:
            open_message_thread(existing_thread.get("id"), back_target)
            return
        app_state["detail_artist"] = artist
        app_state["message_draft"] = {
            "artist_id": artist.get("id"),
            "category": "스타일 상담",
            "content": "",
        }
        app_state["message_back_target"] = back_target
        show_write_artist_message_page()

    def append_thread_message(thread, sender, text):
        thread.setdefault("messages", []).append(
            {
                "sender": sender,
                "text": text,
                "time": datetime.now().strftime("%H:%M"),
            }
        )
        thread["updated_at"] = "방금 전"
        thread["status"] = "답변 완료" if sender == "artist" else "답장 필요"

    def create_customer_message(artist, category, content):
        threads = app_state.setdefault("message_threads", [])
        existing_thread = find_message_thread_by_artist(artist.get("id"))
        if existing_thread:
            append_thread_message(existing_thread, "customer", content)
            existing_thread["category"] = category or existing_thread.get("category", "스타일 상담")
            if existing_thread in threads:
                threads.remove(existing_thread)
            threads.insert(0, existing_thread)
            record_artist_notification(
                "message",
                "새 고객 메시지",
                f'{existing_thread.get("customer_name", "고객")}님이 추가 메시지를 보냈어요.',
                target_page="artist_messages",
            )
            return existing_thread

        thread_id = f"msg_{len(threads) + 1}_{int(datetime.now().timestamp())}"
        current_user = app_state.get("current_user") or {}
        thread = {
            "id": thread_id,
            "artist_id": artist.get("id"),
            "artist_name": artist.get("name", "아티스트"),
            "artist_category": artist.get("category", "헤어"),
            "customer_name": current_user.get("nickname", "FINDY 회원"),
            "category": category or "스타일 상담",
            "status": "답장 필요",
            "updated_at": "방금 전",
            "messages": [
                {
                    "sender": "customer",
                    "text": content,
                    "time": datetime.now().strftime("%H:%M"),
                }
            ],
        }
        threads.insert(0, thread)
        record_artist_notification(
            "message",
            "새 고객 메시지",
            f'{thread["customer_name"]}님이 {thread["category"]} 메시지를 보냈어요.',
            target_page="artist_messages",
        )
        return thread

    def show_completion_feedback_page():
        clear_transient_ui()
        close_overlays()
        feedback = app_state.get("completion_feedback") or {
            "title": "완료되었어요",
            "message": "요청한 작업이 저장되었습니다.",
            "next_label": "돌아가기",
            "next_page": "home",
            "selected_tab": app_state.get("selected_tab", 2),
            "icon": "CHECK_CIRCLE",
        }
        selected_tab = feedback.get("selected_tab")
        if selected_tab is not None:
            app_state["selected_tab"] = selected_tab
        app_state["current_page"] = "completion_feedback"

        def go_next(e=None):
            target = feedback.get("next_page") or "home"
            app_state["completion_feedback"] = None
            app_state["current_page"] = target
            render_current_page()

        body = ft.Column(
            controls=[
                page_header("완료", on_back=go_next),
                ft.Container(height=44),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=28, vertical=42),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                width=70,
                                height=70,
                                border_radius=999,
                                bgcolor=MAIN_COLOR_SOFT,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon(feedback.get("icon", "CHECK_CIRCLE")), size=34, color=MAIN_COLOR),
                            ),
                            ft.Text(feedback.get("title", "완료되었어요"), size=22, color=TEXT_COLOR, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                            ft.Text(feedback.get("message", ""), size=13, color=SUBTEXT_COLOR, height=1.5, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=10),
                            soft_button(feedback.get("next_label", "돌아가기"), MAIN_COLOR, "#FFFFFF", go_next, width=content_width() - 56),
                        ],
                        spacing=14,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state.get("selected_tab", 2))

    def show_artist_approval_pending_page():
        clear_transient_ui()
        close_overlays()
        app_state["current_page"] = "artist_approval_pending"
        app_state["selected_tab"] = 4

        def back_to_login(e=None):
            app_state["current_page"] = "artist_login"
            show_artist_login_page()

        body = ft.Column(
            controls=[
                page_header("승인 대기", on_back=back_to_login),
                ft.Container(height=34),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=26, vertical=38),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            app_logo_block(width=190, compact=True, show_slogan=False),
                            ft.Text("아티스트 승인 대기 중", size=22, color=TEXT_COLOR, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                "명함, 인스타그램, 네이버 플레이스 정보를 확인한 뒤 아티스트 계정을 활성화해요.",
                                size=13,
                                color=SUBTEXT_COLOR,
                                height=1.55,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=4),
                            ft.Container(
                                width=content_width() - 52,
                                padding=SPACE_LG,
                                bgcolor="#FFFFFF",
                                border_radius=RADIUS_LG,
                                border=ft.border.all(1, BORDER_COLOR),
                                content=ft.Column(
                                    controls=[
                                        ft.Text("필요 서류", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text("명함 · 인스타그램 아이디 · 네이버 플레이스 등록 사진", size=12, color=SUBTEXT_COLOR),
                                        ft.Text("승인 전에는 관리 기능을 사용할 수 없어요.", size=11, color=MAIN_COLOR_DARK),
                                    ],
                                    spacing=7,
                                ),
                            ),
                            soft_button("로그인 화면으로", "#FFFFFF", MAIN_COLOR_DARK, back_to_login, border=ft.border.all(1, BORDER_COLOR), width=content_width() - 52),
                        ],
                        spacing=16,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=28),
            ],
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        render_phone_frame(body, None)

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

    def safe_int(value, default=0, minimum=None, maximum=None):
        try:
            result = int(value)
        except (TypeError, ValueError):
            result = default
        if minimum is not None:
            result = max(minimum, result)
        if maximum is not None:
            result = min(maximum, result)
        return result

    def safe_date_fromiso(value, default=None):
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return default

    def generate_reservation_slots(artist=None):
        schedule = get_artist_schedule(artist)
        slot_minutes = safe_int(schedule.get("slot_minutes", 30), default=30, minimum=10)
        try:
            current_slot = datetime.strptime(schedule.get("start", "09:00"), "%H:%M")
            slot_end = datetime.strptime(schedule.get("end", "22:00"), "%H:%M")
        except (TypeError, ValueError):
            current_slot = datetime.strptime(DEFAULT_ARTIST_SCHEDULE["start"], "%H:%M")
            slot_end = datetime.strptime(DEFAULT_ARTIST_SCHEDULE["end"], "%H:%M")
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
        booking_days = safe_int(schedule.get("booking_days", 45), default=45, minimum=7)
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
        current_user = app_state.get("current_user") or {}
        return {
            "id": f'r{len(app_state.get("reservation_history", [])) + 1}',
            "artist_id": form.get("artist_id"),
            "artist_name": form.get("artist_name", ""),
            "customer_name": current_user.get("nickname", "FINDY 회원"),
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
            return True
        except Exception as e:
            print(f"Failed to save reservation history: {e}")
            return False

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
                previous_status = item.get("status")
                previous_cancelled_at = item.get("cancelled_at")
                item["status"] = "예약 취소"
                item["cancelled_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                if not save_reservation_history_to_file():
                    item["status"] = previous_status
                    if previous_cancelled_at is None:
                        item.pop("cancelled_at", None)
                    else:
                        item["cancelled_at"] = previous_cancelled_at
                    show_snack("예약 취소 저장에 실패했어요. 다시 시도해주세요.", bgcolor="#B85C5C")
                    return None
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
        if not save_reservation_history_to_file():
            history.remove(reservation_item)
            app_state["last_completed_reservation"] = None
            show_snack("예약 저장에 실패했어요. 다시 시도해주세요.", bgcolor="#B85C5C")
            return None
        record_artist_notification(
            "artist_reservation",
            "새 예약이 체결되었어요",
            (
                f'{reservation_item.get("customer_name", "고객")} · '
                f'{reservation_item.get("service", reservation_item.get("category", "시술"))} · '
                f'{format_reservation_date_text(reservation_item.get("date"), reservation_item.get("time"))}'
            ),
            target_page="artist_reservations",
        )
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

    def logout_to_login(e=None):
        clear_transient_ui()
        close_overlays()
        app_state["current_user"] = None
        app_state["selected_tab"] = 2
        app_state["page_history"] = []
        if is_artist_runtime():
            app_state["current_page"] = "artist_login"
            show_artist_login_page()
        else:
            app_state["current_page"] = "login"
            show_login_page()

    def logout_button(label="로그아웃", subtitle="현재 계정에서 로그아웃해요."):
        return ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor="#FFFFFF",
            border_radius=22,
            border=ft.border.all(1, BORDER_COLOR),
            ink=True,
            on_click=logout_to_login,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=38,
                        height=38,
                        border_radius=14,
                        bgcolor=CHIP_BG,
                        border=ft.border.all(1, BORDER_COLOR),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=19, color=MAIN_COLOR),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(label, size=14, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            ft.Text(subtitle, size=10, color=SUBTEXT_COLOR, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=14, color=SUBTEXT_COLOR),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

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
                app_state["_suppress_next_history_record"] = True
                app_state["current_page"] = previous_page
                if previous_page == "category":
                    app_state["selected_tab"] = 0
                elif previous_page == "home":
                    app_state["selected_tab"] = 2
                elif previous_page in {"snap", "snap_detail", "write_snap"}:
                    app_state["selected_tab"] = 1
                elif previous_page in {"video", "video_detail", "write_video"}:
                    app_state["selected_tab"] = 3
                elif previous_page in {
                    "customer_messages",
                    "artist_messages",
                    "write_artist_message",
                    "message_detail",
                }:
                    app_state["selected_tab"] = 5
                elif previous_page in {
                    "my",
                    "saved",
                    "reservation_history",
                    "cancelled_treatments",
                    "placeholder_info",
                    "my_reviews",
                    "my_content",
                    "saved_content",
                    "completed",
                    "beauty_profile",
                    "notice",
                    "feedback",
                    "support",
                    "inquiry",
                    "notifications",
                }:
                    app_state["selected_tab"] = 4
                elif str(previous_page).startswith("artist_"):
                    app_state["selected_tab"] = 4
                render_current_page()
                return

        app_state["_suppress_next_history_record"] = True
        if is_artist_runtime():
            app_state["current_page"] = "artist_main"
            app_state["selected_tab"] = 4
            show_artist_main_page()
        else:
            app_state["current_page"] = "home"
            app_state["selected_tab"] = 2
            show_home_page()

    def render_current_page():
        page_name = app_state.get("current_page", "home")
        if page_name == "opening":
            show_opening_page()
        elif page_name == "login":
            show_login_page()
        elif page_name == "signup":
            show_signup_page("user")
        elif page_name == "artist_login":
            show_artist_login_page()
        elif page_name == "artist_signup":
            show_signup_page("artist")
        elif page_name == "artist_approval_pending":
            show_artist_approval_pending_page()
        elif page_name == "completion_feedback":
            show_completion_feedback_page()
        elif page_name == "home_category_transition":
            show_home_page()
        elif page_name == "home":
            show_home_page()
        elif page_name == "category":
            show_category_page()
        elif page_name == "snap":
            show_snap_page()
        elif page_name == "search":
            show_search_page()
        elif page_name == "search_results":
            show_search_results_page()
        elif page_name == "my":
            show_my_page()
        elif page_name == "artist_main":
            show_artist_main_page()
        elif page_name == "artist_profile_preview":
            show_artist_profile_preview_page()
        elif page_name == "artist_profile_post":
            show_artist_profile_post_page()
        elif page_name == "artist_portfolio":
            show_artist_portfolio_page()
        elif page_name == "artist_portfolio_add":
            show_artist_portfolio_add_page()
        elif page_name == "artist_profile":
            show_artist_profile_page()
        elif page_name == "artist_reservations":
            show_artist_reservation_manage_page()
        elif page_name == "artist_reviews":
            show_artist_review_manage_page()
        elif page_name == "artist_trend_analysis":
            show_artist_trend_analysis_page()
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
        elif page_name == "video_detail":
            show_video_detail_page()
        elif page_name == "my_content":
            show_my_content_page()
        elif page_name == "saved_content":
            show_saved_content_page()
        elif page_name == "content_detail":
            show_content_detail_page()
        elif page_name == "artist_time_manage":
            show_artist_time_manage_page()
        elif page_name == "artist_price_menu":
            show_artist_price_menu_page()
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
        elif page_name == "customer_messages":
            show_customer_messages_page()
        elif page_name == "artist_messages":
            show_artist_messages_page()
        elif page_name == "message_artist_search":
            show_message_artist_search_page()
        elif page_name == "write_artist_message":
            show_write_artist_message_page()
        elif page_name == "message_detail":
            show_message_detail_page()
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
            if is_artist_runtime() or is_artist_manage_mode():
                show_artist_main_page()
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
        if is_artist_manage_mode():
            show_snack("아티스트 계정에서는 검색 기능을 사용할 수 없어요.", bgcolor="#B85C5C")
            return

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

    def build_artist_content_search_results(query):
        query = (query or "").strip()
        if not query:
            return []

        results = []

        for category_name in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]:
            for item in get_snap_feed_items("recommended", category_name):
                if matches_query(query, item.get("title"), item.get("category")):
                    results.append({
                        "type": "snap",
                        "snap_id": item.get("id"),
                        "category": item.get("category"),
                        "title": item.get("title", "스냅"),
                        "subtitle": "고객 반응이 있는 스냅",
                        "meta": f"좋아요 {item.get('likes', 0)} · 저장 {item.get('saves', 0)} · 조회 {item.get('views', 0)}",
                        "description": "고객들이 반응한 스타일 스냅이에요.",
                        "badge": "스냅",
                    })

        for name, category, review in get_review_items():
            if matches_query(query, name, category, review):
                results.append({
                    "type": "review",
                    "category": category,
                    "title": f"{name}님의 리뷰",
                    "subtitle": category,
                    "meta": "고객 리뷰",
                    "description": review,
                    "badge": "리뷰",
                })

        for post in app_state.get("community_posts", []):
            if matches_query(
                query,
                post.get("title"),
                post.get("category"),
                post.get("post_type"),
                post.get("type"),
                post.get("body"),
                post.get("description"),
            ):
                results.append({
                    "type": "community",
                    "category": post.get("category", "커뮤니티"),
                    "title": post.get("title", "커뮤니티 글"),
                    "subtitle": post.get("post_type") or post.get("type") or "커뮤니티",
                    "meta": post.get("meta", "고객 커뮤니티 글"),
                    "description": post.get("body") or post.get("description") or "고객들이 남긴 이야기예요.",
                    "badge": "커뮤니티",
                })

        for video in app_state.get("written_videos", []):
            if matches_query(query, video.get("title"), video.get("subtitle"), video.get("category")):
                results.append({
                    "type": "video",
                    "category": video.get("category", "비디오"),
                    "title": video.get("title", "비디오"),
                    "subtitle": video.get("subtitle", "스타일 영상"),
                    "meta": f"{video.get('duration', '0:00')} · 조회 {video.get('views', '0')}",
                    "description": "업로드된 스타일 영상이에요.",
                    "badge": "비디오",
                })

        return results

    def submit_artist_content_search(query):
        query = (query or "").strip()
        if not query:
            show_snack("검색어를 입력해주세요.", bgcolor="#B85C5C")
            return

        app_state["search_text"] = query
        app_state["selected_category"] = None
        app_state["selected_subcategory"] = "통합검색"
        app_state["search_results"] = build_artist_content_search_results(query)
        app_state["recommendation_entry"] = query
        app_state["category_browse_mode"] = True
        app_state["search_results_back_target"] = "home"
        app_state["selected_tab"] = 2
        app_state["current_page"] = "search_results"
        show_search_results_page()

    def artist_trend_dataset():
        return {
            "일별": [
                {"title": "레이어드컷", "category": "헤어", "searches": 1800, "likes": 355, "saves": 144, "change": 18, "keywords": ["가벼운 층", "얼굴형 보정", "내추럴"]},
                {"title": "글로시 핑크 네일", "category": "네일아트", "searches": 1400, "likes": 296, "saves": 138, "change": 14, "keywords": ["시럽", "짧은 손톱", "데일리"]},
                {"title": "윤광 베이스", "category": "메이크업", "searches": 1200, "likes": 287, "saves": 120, "change": 11, "keywords": ["촉촉", "피부표현", "자연스러움"]},
                {"title": "브라이드 무드 스냅", "category": "웨딩", "searches": 1050, "likes": 366, "saves": 171, "change": 10, "keywords": ["신부", "본식", "화사함"]},
                {"title": "감성 프로필 포토", "category": "포토", "searches": 980, "likes": 278, "saves": 117, "change": 9, "keywords": ["자연광", "프로필", "따뜻함"]},
                {"title": "아이라인 포인트", "category": "반영구", "searches": 860, "likes": 198, "saves": 89, "change": 8, "keywords": ["또렷함", "자연", "유지력"]},
            ],
            "주별": [
                {"title": "빌드펌 무드컷", "category": "헤어", "searches": 5600, "likes": 355, "saves": 163, "change": 22, "keywords": ["볼륨", "굵은 웨이브", "여성스러움"]},
                {"title": "자연눈썹", "category": "반영구", "searches": 4100, "likes": 214, "saves": 96, "change": 17, "keywords": ["민낯", "결", "자연"]},
                {"title": "웨딩 피치 메이크업", "category": "웨딩", "searches": 3800, "likes": 274, "saves": 152, "change": 13, "keywords": ["피치", "화사함", "본식"]},
                {"title": "화이트 프렌치 네일", "category": "네일아트", "searches": 3400, "likes": 334, "saves": 166, "change": 12, "keywords": ["깔끔", "웨딩", "프렌치"]},
                {"title": "로지 포인트 메이크업", "category": "메이크업", "searches": 3100, "likes": 226, "saves": 101, "change": 10, "keywords": ["로지", "생기", "데일리"]},
                {"title": "데일리 무드 촬영", "category": "포토", "searches": 2800, "likes": 247, "saves": 104, "change": 9, "keywords": ["컨셉", "감성", "일상"]},
            ],
            "월별": [
                {"title": "프로필 스냅", "category": "포토", "searches": 19000, "likes": 278, "saves": 117, "change": 31, "keywords": ["프로필", "컨셉", "자연광"]},
                {"title": "애쉬 브라운 컬러", "category": "헤어", "searches": 15000, "likes": 264, "saves": 111, "change": 24, "keywords": ["차분", "브라운", "톤다운"]},
                {"title": "리본 포인트 네일", "category": "네일아트", "searches": 12000, "likes": 309, "saves": 142, "change": 19, "keywords": ["리본", "러블리", "포인트"]},
                {"title": "봄 라이트 메이크업", "category": "메이크업", "searches": 10800, "likes": 242, "saves": 109, "change": 16, "keywords": ["봄웜", "라이트", "맑음"]},
                {"title": "본식 헤어메이크업", "category": "웨딩", "searches": 9700, "likes": 302, "saves": 145, "change": 15, "keywords": ["본식", "신부", "단정"]},
                {"title": "입술 컬러 시술", "category": "반영구", "searches": 7900, "likes": 188, "saves": 86, "change": 11, "keywords": ["생기", "틴트", "자연"]},
            ],
        }

    def artist_trend_items(period=None, category=None):
        selected_period = period or app_state.get("artist_trend_period", "주별")
        selected_category = category or app_state.get("artist_trend_category", "헤어")
        return artist_category_flow_items(selected_period, selected_category)

    def artist_category_flow_items(period, category):
        if category == "전체":
            return list(artist_trend_dataset().get(period, []))

        category_styles = {
            "헤어": [
                {"title": "레이어드컷", "searches": 6200, "likes": 355, "saves": 144, "change": 22, "keywords": ["중단발", "얼굴형 보정", "레이어드펌"]},
                {"title": "빌드펌", "searches": 5600, "likes": 338, "saves": 163, "change": 20, "keywords": ["굵은 웨이브", "뿌리볼륨", "손질 쉬운"]},
                {"title": "애쉬 브라운 컬러", "searches": 4800, "likes": 264, "saves": 111, "change": 17, "keywords": ["톤다운", "쿨브라운", "염색"]},
                {"title": "시크 블랙 단발", "searches": 3900, "likes": 205, "saves": 88, "change": 12, "keywords": ["태슬컷", "단발", "차분한"]},
            ],
            "네일아트": [
                {"title": "화이트 프렌치 네일", "searches": 5200, "likes": 334, "saves": 166, "change": 19, "keywords": ["웨딩네일", "깔끔한 네일", "짧은 손톱"]},
                {"title": "리본 포인트 네일", "searches": 4700, "likes": 309, "saves": 142, "change": 17, "keywords": ["러블리", "핑크", "파츠"]},
                {"title": "글로시 핑크 네일", "searches": 4300, "likes": 296, "saves": 138, "change": 14, "keywords": ["시럽네일", "데일리", "투명감"]},
                {"title": "무드 파츠 네일", "searches": 3100, "likes": 190, "saves": 81, "change": 9, "keywords": ["실버파츠", "블랙네일", "포인트"]},
            ],
            "메이크업": [
                {"title": "윤광 베이스", "searches": 4500, "likes": 287, "saves": 120, "change": 16, "keywords": ["피부표현", "촉촉한", "민낯메이크업"]},
                {"title": "로지 포인트 메이크업", "searches": 3900, "likes": 226, "saves": 101, "change": 12, "keywords": ["생기", "블러셔", "데일리"]},
                {"title": "봄 라이트 메이크업", "searches": 3600, "likes": 242, "saves": 109, "change": 11, "keywords": ["봄웜", "라이트톤", "맑은 메이크업"]},
                {"title": "데일리 소프트 음영", "searches": 2800, "likes": 181, "saves": 76, "change": 8, "keywords": ["음영", "출근 메이크업", "브라운"]},
            ],
            "반영구": [
                {"title": "자연눈썹", "searches": 4100, "likes": 214, "saves": 96, "change": 17, "keywords": ["눈썹결", "민낯", "남자눈썹"]},
                {"title": "입술 컬러 시술", "searches": 3300, "likes": 188, "saves": 86, "change": 11, "keywords": ["틴트입술", "생기", "자연발색"]},
                {"title": "아이라인 포인트", "searches": 2700, "likes": 198, "saves": 89, "change": 9, "keywords": ["또렷한 눈매", "유지력", "자연라인"]},
                {"title": "헤어라인 보정", "searches": 2100, "likes": 146, "saves": 61, "change": 6, "keywords": ["잔머리", "이마라인", "M자"]},
            ],
            "웨딩": [
                {"title": "웨딩 피치 메이크업", "searches": 3800, "likes": 274, "saves": 152, "change": 13, "keywords": ["본식", "피치톤", "신부화장"]},
                {"title": "본식 헤어메이크업", "searches": 3600, "likes": 302, "saves": 145, "change": 12, "keywords": ["로우번", "드레스", "단정한"]},
                {"title": "브라이드 무드 스냅", "searches": 3200, "likes": 366, "saves": 171, "change": 10, "keywords": ["웨딩스냅", "화사한", "신부"]},
                {"title": "하객 스타일링", "searches": 2400, "likes": 174, "saves": 78, "change": 7, "keywords": ["하객룩", "깔끔한", "고급"]},
            ],
            "포토": [
                {"title": "프로필 스냅", "searches": 5200, "likes": 278, "saves": 117, "change": 31, "keywords": ["자연광", "취업사진", "배우프로필"]},
                {"title": "데일리 무드 촬영", "searches": 4100, "likes": 247, "saves": 104, "change": 18, "keywords": ["감성사진", "일상스냅", "따뜻한"]},
                {"title": "컨셉 포토", "searches": 3600, "likes": 221, "saves": 92, "change": 14, "keywords": ["스튜디오", "화보", "선명한"]},
                {"title": "자연광 포트레이트", "searches": 2900, "likes": 184, "saves": 74, "change": 9, "keywords": ["인물사진", "야외촬영", "맑은"]},
            ],
        }
        period_scale = {"일별": 0.34, "주별": 1, "월별": 3.35}
        period_change = {"일별": -4, "주별": 0, "월별": 6}
        scale = period_scale.get(period, 1)
        change_delta = period_change.get(period, 0)
        items = []
        for item in category_styles.get(category, []):
            copied = item.copy()
            copied["category"] = category
            copied["searches"] = int(copied["searches"] * scale)
            copied["likes"] = int(copied["likes"] * (0.55 if period == "일별" else 1.0 if period == "주별" else 1.8))
            copied["saves"] = int(copied["saves"] * (0.5 if period == "일별" else 1.0 if period == "주별" else 1.65))
            copied["change"] = max(3, copied["change"] + change_delta)
            items.append(copied)
        return items

    def trend_number(value):
        if value >= 10000:
            return f"{value / 10000:.1f}만"
        if value >= 1000:
            return f"{value / 1000:.1f}천"
        return str(value)

    def build_category_browse_items(main_category, sub_category):
        normalized_category = normalize_overlay_category_name(main_category)
        category_artists = [a.copy() for a in base_artists if a["category"] == normalized_category]

        if normalized_category == "전체":
            beauty_categories = ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
            if sub_category == "아티스트":
                all_artists = []
                for category in beauty_categories:
                    category_key = normalize_overlay_category_name(category)
                    all_artists.extend([artist.copy() for artist in base_artists if artist["category"] == category_key])
                return all_artists
            if sub_category == "샵":
                all_shops = []
                for category in beauty_categories:
                    all_shops.extend(build_category_browse_items(category, "샵"))
                return all_shops
            if sub_category == "리뷰":
                all_reviews = []
                for category in beauty_categories:
                    all_reviews.extend(build_category_browse_items(category, "리뷰"))
                return all_reviews
            if sub_category in {"커뮤니티", "카테고리"}:
                all_community_posts = []
                for category in beauty_categories:
                    all_community_posts.extend(build_category_browse_items(category, "커뮤니티"))
                return all_community_posts

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
                    "category": normalized_category,
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
                    "category": normalized_category,
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
                    "category": normalized_category,
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
                    "category": main_category,
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
            open_completion_feedback(
                "커뮤니티 글이 등록되었어요",
                "작성한 글은 커뮤니티 목록에서 확인할 수 있어요.",
                "커뮤니티 보기",
                "search_results",
                selected_tab=0,
                icon_name="FORUM",
            )

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
            bgcolor=CARD_COLOR,
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
                                bgcolor=CHIP_BG,
                                border=ft.border.all(1, BORDER_COLOR),
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
                                bgcolor=CARD_COLOR,
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
                                bgcolor=CARD_COLOR,
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
                                bgcolor=CARD_COLOR,
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
        row_bgcolor = CARD_COLOR if enabled else "#FFFFFF"

        trailing_controls = []
        if badge_text:
            trailing_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=CHIP_BG if enabled else CARD_COLOR,
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
                            ft.Text(
                                label,
                                size=15,
                                color=text_color,
                                weight=ft.FontWeight.W_500,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                        ],
                        spacing=SPACE_MD,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
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
            bgcolor=CARD_COLOR,
            border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
            on_click=on_click if enabled else None,
            ink=enabled and on_click is not None,
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=6, height=6, border_radius=999, bgcolor=MAIN_COLOR),
                            ft.Text(
                                label,
                                size=13,
                                color=text_color,
                                weight=ft.FontWeight.W_500,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
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
            ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(subtitle, size=11, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
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
        can_write_review = not is_artist_manage_mode()

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
                write_review_banner if can_write_review else ft.Container(),
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
        if is_artist_manage_mode():
            show_snack("아티스트 계정에서는 리뷰를 작성할 수 없어요.", bgcolor="#B85C5C")
            show_artist_main_page()
            return
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

        artist_option_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
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

        photos_row = ft.Row(controls=[], spacing=8, scroll=ft.ScrollMode.HIDDEN)
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
            app_state["review_target"] = None
            open_completion_feedback(
                "리뷰가 등록되었어요",
                "작성한 리뷰는 내 활동과 리뷰 목록에서 확인할 수 있어요.",
                "예약내역 보기",
                "reservation_history",
                selected_tab=4,
                icon_name="RATE_REVIEW",
            )

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

    def make_simple_content_item(content_type, title, subtitle="", description="", badge=None, meta="", source=None):
        return {
            "type": content_type,
            "id": source.get("id") if isinstance(source, dict) else None,
            "title": title or content_type,
            "subtitle": subtitle or content_type,
            "description": description or "",
            "badge": badge or content_type,
            "meta": meta,
            "source": source,
        }

    def content_identity(item):
        if not isinstance(item, dict):
            return str(item)
        source = item.get("source")
        if isinstance(source, dict) and source.get("id"):
            return source.get("id")
        return item.get("id") or f'{item.get("badge", "content")}:{item.get("title", "")}:{item.get("subtitle", "")}'

    def is_content_hidden(item):
        return content_identity(item) in app_state.get("hidden_content_ids", set())

    def video_key(video):
        return video.get("id") or f'{video.get("category", "")}:{video.get("title", "")}:{video.get("subtitle", "")}'

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
            {"id": "video_hair_1", "title": "레이어드컷 완성 과정", "subtitle": "자연스럽게 층 내는 법 총정리", "badge": "SHORTS", "category": "헤어", "duration": "0:58", "views": "3.2만"},
            {"id": "video_hair_2", "title": "빌드펌 시술 타임랩스", "subtitle": "굵은 웨이브 연출 하이라이트", "badge": "REELS", "category": "헤어", "duration": "0:59", "views": "2.8만"},
            {"id": "video_makeup_1", "title": "윤광 베이스 메이크업", "subtitle": "5분 완성 데일리 베이스", "badge": "SHORTS", "category": "메이크업", "duration": "0:52", "views": "4.1만"},
            {"id": "video_makeup_2", "title": "웨딩 피치 메이크업", "subtitle": "본식 당일 메이크업 하이라이트", "badge": "TREND", "category": "메이크업", "duration": "0:57", "views": "5.6만"},
            {"id": "video_nail_1", "title": "글로시 핑크 네일 시술", "subtitle": "아이디어가 되는 네일 무드", "badge": "SHORTS", "category": "네일아트", "duration": "0:45", "views": "2.1만"},
            {"id": "video_nail_2", "title": "파츠 아트 네일 디테일컷", "subtitle": "트렌드 파츠 배치 영상", "badge": "REELS", "category": "네일아트", "duration": "0:55", "views": "1.9만"},
            {"id": "video_wedding_1", "title": "브라이드 무드 헤어메이크업", "subtitle": "본식 스타일링 하이라이트", "badge": "TREND", "category": "웨딩", "duration": "0:58", "views": "6.3만"},
            {"id": "video_wedding_2", "title": "하객 스타일링 루틴", "subtitle": "결혼식 참석룩 완성하기", "badge": "SHORTS", "category": "웨딩", "duration": "0:54", "views": "3.7만"},
            {"id": "video_photo_1", "title": "감성 프로필 포토 촬영 BTS", "subtitle": "자연광 촬영 세팅 공개", "badge": "REELS", "category": "포토", "duration": "0:56", "views": "2.5만"},
            {"id": "video_photo_2", "title": "데일리 무드 셀프 촬영법", "subtitle": "폰으로 찍는 감성 포토 팁", "badge": "TREND", "category": "포토", "duration": "0:49", "views": "4.4만"},
        ]

    def get_all_video_items():
        written = []
        for idx, item in enumerate(app_state.get("written_videos", []), start=1):
            copied = item.copy()
            copied.setdefault("id", f"written_video_{idx}")
            written.append(copied)
        return [item for item in written + default_video_items() if is_short_video(item)]

    def open_content_detail(item, back_page="my_content"):
        app_state["content_detail_item"] = item
        app_state["content_detail_back_page"] = back_page
        app_state["current_page"] = "content_detail"
        show_content_detail_page()

    def show_content_detail_page(item=None):
        if item is not None:
            app_state["content_detail_item"] = item
        item = app_state.get("content_detail_item") or {}
        app_state["current_page"] = "content_detail"
        app_state["selected_tab"] = 4

        back_page = app_state.get("content_detail_back_page", "my_content")
        def go_back(e=None):
            if back_page == "saved_content":
                show_saved_content_page()
            elif back_page == "search_results":
                show_search_results_page()
            else:
                show_my_content_page()

        photos = item.get("photos") or []
        content_id = content_identity(item)

        def report_content(e=None):
            app_state.setdefault("reported_content_ids", set()).add(content_id)
            show_snack("신고가 접수되었어요. 운영팀이 확인할게요.")

        def hide_content(e=None):
            app_state.setdefault("hidden_content_ids", set()).add(content_id)
            show_snack("이 글을 숨겼어요.")
            go_back()

        content_controls = [
            page_header(item.get("badge") or "전체글", on_back=go_back),
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
                                ft.Column(
                                    controls=[
                                        ft.Text(item.get("title", "제목 없음"), size=18, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                                        ft.Text(item.get("subtitle") or item.get("meta") or "", size=12, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=11, vertical=7),
                                    bgcolor=MAIN_COLOR_SOFT,
                                    border_radius=999,
                                    content=ft.Text(item.get("badge", "글"), size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Container(height=1, bgcolor=BORDER_COLOR),
                        ft.Text(item.get("description", "내용이 없어요."), size=14, color=TEXT_COLOR, height=1.65),
                    ],
                    spacing=14,
                ),
            ),
        ]
        if photos:
            content_controls.append(
                ft.Container(
                    width=content_width(),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=96,
                                height=96,
                                border_radius=12,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Image(src=photo, width=96, height=96, fit=ft.ImageFit.COVER),
                            )
                            for photo in photos[:10]
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.HIDDEN,
                    ),
                )
            )
        content_controls.append(
            ft.Container(
                width=content_width(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=14, vertical=12),
                            bgcolor="#FFFFFF",
                            border_radius=999,
                            border=ft.border.all(1, BORDER_COLOR),
                            ink=True,
                            on_click=report_content,
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.FLAG_OUTLINED, size=16, color=SUBTEXT_COLOR),
                                    ft.Text("신고", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                ],
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=14, vertical=12),
                            bgcolor="#FFFFFF",
                            border_radius=999,
                            border=ft.border.all(1, BORDER_COLOR),
                            ink=True,
                            on_click=hide_content,
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.VISIBILITY_OFF_OUTLINED, size=16, color=SUBTEXT_COLOR),
                                    ft.Text("숨김", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                ],
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ),
                    ],
                    spacing=8,
                ),
            )
        )
        content_controls.append(ft.Container(height=24))
        make_shell(
            ft.Column(controls=content_controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            app_state["selected_tab"],
        )

    def show_my_content_page(content_type=None):
        if content_type:
            app_state["my_content_type"] = content_type
        content_type = app_state.get("my_content_type", "스냅")
        app_state["current_page"] = "my_content"
        app_state["selected_tab"] = 4

        if content_type == "스냅":
            raw_items = app_state.get("written_snaps", [])
            items = [
                make_simple_content_item(
                    "snap",
                    item.get("title"),
                    f'{item.get("category", "스냅")} · {item.get("artist_name", "아티스트")}',
                    item.get("description", ""),
                    "스냅",
                    f'좋아요 {item.get("likes", 0)} · 저장 {item.get("saves", 0)}',
                    item,
                )
                for item in raw_items
            ]
        elif content_type == "비디오":
            raw_items = app_state.get("written_videos", [])
            items = [
                make_simple_content_item(
                    "video",
                    item.get("title"),
                    f'{item.get("category", "비디오")} · {item.get("duration", "0:00")}',
                    item.get("subtitle", ""),
                    "비디오",
                    f'조회 {item.get("views", "0")}',
                    item,
                )
                for item in raw_items
            ]
        else:
            raw_items = app_state.get("community_posts", [])
            items = [
                make_simple_content_item(
                    "community",
                    item.get("title", "커뮤니티 글"),
                    f'{item.get("category", "커뮤니티")} · {item.get("post_type", item.get("badge", "커뮤니티"))}',
                    item.get("description") or item.get("body", ""),
                    "커뮤니티",
                    item.get("meta", "댓글 0 · 저장 0"),
                    item,
                )
                for item in raw_items
            ]

        def open_item(item):
            def handler(e):
                source = item.get("source") or item
                if item["type"] == "snap":
                    open_snap_detail(source)
                elif item["type"] == "video":
                    show_video_detail_page(source)
                else:
                    open_content_detail(item, back_page="my_content")
            return handler

        controls = [
            page_header(f"내가 쓴 {content_type}", on_back=go_back_page),
            ft.Text(f"작성한 {content_type} 콘텐츠를 모아봤어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
        ]
        visible_items = [item for item in items if not is_content_hidden(item)]
        if visible_items:
            controls.extend([browse_result_card(item, on_click=open_item(item)) for item in visible_items])
        else:
            write_target = {"스냅": show_write_snap_page, "비디오": show_write_video_page, "커뮤니티": show_write_community_page}.get(content_type, show_my_page)
            controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(f"아직 작성한 {content_type}이 없어요.", size=15, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("첫 콘텐츠를 작성하면 이곳에서 바로 확인할 수 있어요.", size=12, color=SUBTEXT_COLOR),
                            soft_button(f"{content_type} 작성하기", MAIN_COLOR, "white", lambda e: write_target(), width=content_width() - 48),
                        ],
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        controls.append(ft.Container(height=24))
        make_shell(ft.Column(controls=controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER), app_state["selected_tab"])

    def show_saved_content_page(content_type=None):
        if content_type:
            app_state["saved_content_type"] = content_type
        content_type = app_state.get("saved_content_type", "아티스트")
        app_state["current_page"] = "saved_content"
        app_state["selected_tab"] = 4

        items = []
        if content_type == "샵":
            saved_artists = [find_artist_by_id(aid) for aid in app_state.get("saved_ids", set())]
            for artist in [a for a in saved_artists if a]:
                items.append(make_simple_content_item("shop", f'{artist["name"].split()[0]} 뷰티 스튜디오', artist["category"], artist["intro"], "샵", f'⭐ {artist["rating"]} · {artist["distance"]}', artist))
        elif content_type == "스냅":
            saved_ids = app_state.get("snap_saved_ids", set())
            for category in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]:
                for snap in get_snap_feed_items("latest", category):
                    if snap.get("id") in saved_ids:
                        items.append(make_simple_content_item("snap", snap.get("title"), snap.get("category"), snap.get("description", ""), "스냅", f'좋아요 {snap.get("likes", 0)} · 저장 {snap.get("saves", 0)}', snap))
        elif content_type == "비디오":
            saved_keys = app_state.get("video_saved_keys", set())
            for video in get_all_video_items():
                if video_key(video) in saved_keys:
                    items.append(make_simple_content_item("video", video.get("title"), video.get("category"), video.get("subtitle", ""), "비디오", f'{video.get("duration", "0:00")} · 조회 {video.get("views", "0")}', video))
        else:
            show_saved_page()
            return

        def open_item(item):
            def handler(e):
                source = item.get("source") or item
                if item["type"] == "snap":
                    open_snap_detail(source)
                elif item["type"] == "video":
                    show_video_detail_page(source)
                elif item["type"] == "shop" and isinstance(source, dict):
                    open_detail(source, back_target="saved")
                else:
                    open_content_detail(item, back_page="saved_content")
            return handler

        controls = [
            page_header(f"저장한 {content_type}", on_back=go_back_page),
            ft.Text(f"저장한 {content_type} 항목을 모아봤어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
        ]
        visible_items = [item for item in items if not is_content_hidden(item)]
        if visible_items:
            controls.extend([browse_result_card(item, on_click=open_item(item)) for item in visible_items])
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
                            ft.Text(f"아직 저장한 {content_type}이 없어요.", size=15, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("좋아요/저장 버튼을 누르면 이곳에 모여요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        controls.append(ft.Container(height=24))
        make_shell(ft.Column(controls=controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER), app_state["selected_tab"])

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
        can_write_review = not is_artist_manage_mode()

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
                        scroll=ft.ScrollMode.HIDDEN,
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
                write_review_button if can_write_review else ft.Container(),
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
                write_review_button if can_write_review else ft.Container(),
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
            elif not is_artist_manage_mode():
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
                        scroll=ft.ScrollMode.HIDDEN,
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
                    {"label": "스냅", "action": lambda e: (close_overlays(), show_my_content_page("스냅"))},
                    {"label": "비디오", "action": lambda e: (close_overlays(), show_my_content_page("비디오"))},
                    {"label": "커뮤니티", "action": lambda e: (close_overlays(), show_my_content_page("커뮤니티"))},
                ],
            },
            {
                "label": "저장한 뷰티",
                "icon_name": "BOOKMARK_BORDER",
                "action": lambda e: (close_overlays(), show_saved_page()),
                "enabled": True,
                "children": [
                    {"label": "샵", "action": lambda e: (close_overlays(), show_saved_content_page("샵"))},
                    {"label": "아티스트", "action": lambda e: (close_overlays(), show_saved_page())},
                    {"label": "스냅", "action": lambda e: (close_overlays(), show_saved_content_page("스냅"))},
                    {"label": "비디오", "action": lambda e: (close_overlays(), show_saved_content_page("비디오"))},
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
                "label": "메시지",
                "icon_name": "CHAT_BUBBLE_OUTLINE",
                "action": lambda e: (close_overlays(), show_customer_messages_page()),
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
            active = selected_index == index
            icon_color = MAIN_COLOR if active else SUBTEXT_COLOR
            text_color = MAIN_COLOR if active else SUBTEXT_COLOR
            bg_color = ft.Colors.with_opacity(0.08, MAIN_COLOR) if active else ft.Colors.TRANSPARENT
            icon_value = app_icon(active_icon_name if active else icon_name)

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
                        ft.Text(label, size=9, color=text_color, weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_600),
                    ],
                    spacing=1,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        is_artist_nav = is_artist_runtime() or is_artist_manage_mode()
        nav_controls = (
            [
                nav_item("MENU", "MENU", "카테고리", 0, open_left_menu),
                nav_item("PHOTO_LIBRARY_OUTLINED", "PHOTO_LIBRARY", "스냅", 1, go_snap_page),
                nav_item("SMART_DISPLAY_OUTLINED", "SMART_DISPLAY", "비디오", 3, go_video_page),
                nav_item("HOME_OUTLINED", "HOME", "홈", 2, go_home_page),
                nav_item("CHAT_BUBBLE_OUTLINE", "CHAT_BUBBLE", "메시지", 5, show_artist_messages_page),
                nav_item("PERSON_OUTLINE", "PERSON", "관리", 4, show_artist_main_page),
            ]
            if is_artist_nav
            else [
                nav_item("MENU", "MENU", "카테고리", 0, open_left_menu),
                nav_item("PHOTO_LIBRARY_OUTLINED", "PHOTO_LIBRARY", "스냅", 1, go_snap_page),
                nav_item("SMART_DISPLAY_OUTLINED", "SMART_DISPLAY", "비디오", 3, go_video_page),
                nav_item("HOME_OUTLINED", "HOME", "홈", 2, go_home_page),
                nav_item("CHAT_BUBBLE_OUTLINE", "CHAT_BUBBLE", "메시지", 5, show_customer_messages_page),
                nav_item("PERSON_OUTLINE", "PERSON", "내정보", 4, open_right_menu),
            ]
        )

        return ft.Container(
            height=62,
            margin=ft.margin.only(left=0, right=0, bottom=0, top=0),
            padding=ft.padding.only(left=8, right=8, top=4, bottom=6),
            bgcolor=ft.Colors.with_opacity(0.98, BG_COLOR),
            border_radius=ft.border_radius.only(top_left=22, top_right=22, bottom_left=0, bottom_right=0),
            border=ft.border.only(top=ft.BorderSide(0.8, ft.Colors.with_opacity(0.24, BORDER_COLOR))),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color="#12000000",
                offset=ft.Offset(0, -1),
            ),
            content=ft.Row(
                controls=nav_controls,
                spacing=6,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    def render_phone_frame(body_content, nav_index=None):
        current_page = app_state.get("current_page", "home")
        last_page = app_state.get("_last_rendered_page")
        page_changed = current_page != last_page
        suppress_history_record = bool(app_state.pop("_suppress_next_history_record", False))
        auth_transition_pages = {"login", "signup", "artist_login", "artist_signup", "opening"}
        auth_destination_pages = {"home", "artist_main"}
        if page_changed:
            if (
                not suppress_history_record
                and last_page
                and last_page != current_page
                and not (last_page in auth_transition_pages and current_page in auth_destination_pages)
            ):
                history = app_state.setdefault("page_history", [])
                if not history or history[-1] != last_page:
                    history.append(last_page)
            app_state["_last_rendered_page"] = current_page
        preserve_scroll_pages = {
            "category",
            "search",
            "search_results",
            "reservation",
            "reservation_confirm",
            "reservation_complete",
            "my",
            "saved",
            "detail",
            "review",
            "write_review",
            "snap",
            "snap_detail",
            "write_snap",
            "write_community",
            "video",
            "video_detail",
            "write_video",
            "my_content",
            "saved_content",
            "content_detail",
            "reservation_history",
            "cancelled_treatments",
            "my_reviews",
            "completed",
            "customer_messages",
            "artist_messages",
            "message_artist_search",
            "write_artist_message",
            "message_detail",
            "beauty_profile",
            "notice",
            "feedback",
            "support",
            "inquiry",
            "notifications",
            "placeholder_info",
            "artist_main",
            "artist_profile_preview",
            "artist_portfolio",
            "artist_portfolio_add",
            "artist_profile",
            "artist_reservations",
            "artist_time_manage",
            "artist_reviews",
            "artist_trend_analysis",
            "artist_price_menu",
        }
        full_height_pages = {"login", "signup", "artist_signup", "artist_login"}
        nav_safe_bottom = (NAV_BAR_HEIGHT + NAV_SAFE_GAP) if nav_index is not None else 12
        nav_spacer = ft.Container(height=nav_safe_bottom)

        if current_page in preserve_scroll_pages:
            scroll_offset_key = f"{current_page}_scroll_offset"

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
                    scroll=ft.ScrollMode.HIDDEN,
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
                await asyncio.sleep(0.01 if page_changed else 0)
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
                        bgcolor=CARD_COLOR,
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
            scroll=ft.ScrollMode.HIDDEN,
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
            scroll=ft.ScrollMode.HIDDEN,
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

        def inquiry_click(e):
            e.stop_propagation = True
            start_customer_chat_with_artist(artist, "search_results")

        action_controls = [
            ft.Container(
                on_click=save_click,
                ink=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=CHIP_BG,
                border_radius=4,
                content=ft.Text("저장됨" if saved else "저장", size=12, color=TEXT_COLOR),
            )
        ]
        if not (is_artist_runtime() or is_artist_manage_mode()):
            action_controls.append(
                ft.Container(
                    on_click=inquiry_click,
                    ink=True,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, BORDER_COLOR),
                    border_radius=4,
                    content=ft.Text("메시지", size=12, color=MAIN_COLOR, weight=ft.FontWeight.W_700),
                )
            )
        action_controls.append(
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=MAIN_COLOR,
                border_radius=4,
                content=ft.Text("상세보기", size=12, color="white"),
            )
        )

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
                        controls=action_controls,
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
        app_state["current_page"] = "opening"

        mark_shell_path = resolve_asset_file("app_logo/app_findy_logo_mark_shell.png")
        wordmark_path = resolve_asset_file("app_logo/app_findy_logo_wordmark.png")
        logo_width = 178
        logo_height = logo_width * 386 / 760
        pupil_size = logo_width * 0.13
        pupil_y = logo_height * 0.61 - pupil_size / 2
        left_pupil_base = logo_width * 0.317 - pupil_size / 2
        right_pupil_base = logo_width * 0.684 - pupil_size / 2
        pupil_shift = logo_width * 0.034

        left_pupil = ft.Container(
            left=left_pupil_base,
            top=pupil_y,
            width=pupil_size,
            height=pupil_size,
            border_radius=999,
            bgcolor=LOGO_COLOR,
        )
        right_pupil = ft.Container(
            left=right_pupil_base,
            top=pupil_y,
            width=pupil_size,
            height=pupil_size,
            border_radius=999,
            bgcolor=LOGO_COLOR,
        )
        opening_mark = ft.Container(
            width=logo_width,
            height=logo_height,
            alignment=ft.Alignment(0, 0),
            offset=ft.Offset(0, 0),
            rotate=ft.Rotate(0, alignment=ft.Alignment(0, 0.18)),
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Stack(
                width=logo_width,
                height=logo_height,
                controls=[
                    (
                        ft.Image(src=mark_shell_path, width=logo_width, height=logo_height, fit=ft.ImageFit.CONTAIN)
                        if mark_shell_path
                        else ft.Icon(ft.Icons.TRAVEL_EXPLORE, size=logo_width, color=LOGO_COLOR)
                    ),
                    left_pupil,
                    right_pupil,
                ],
            ),
        )
        opening_wordmark = (
            ft.Image(src=wordmark_path, width=136, height=30, fit=ft.ImageFit.CONTAIN)
            if wordmark_path
            else ft.Text("FINDY", size=30, weight=ft.FontWeight.W_800, color=LOGO_COLOR)
        )
        opening_image = ft.Container(
            width=full_phone_width(),
            height=PHONE_HEIGHT,
            opacity=0,
            animate_opacity=ft.Animation(420, ft.AnimationCurve.EASE_IN_OUT),
            alignment=ft.Alignment(0, 0.02),
            content=ft.Column(
                controls=[
                    opening_mark,
                    ft.Container(height=16),
                    opening_wordmark,
                    ft.Container(height=54),
                    ft.Text("Find Your Beauty", size=17, color=LOGO_COLOR, weight=ft.FontWeight.W_400),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

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
        opening_image.opacity = 1
        image_holder.scale = 1.0
        opening_overlay.opacity = 0.0
        page.update()

        async def animate_opening_logo():
            frames = [0, -1, 1, 0]
            while app_state.get("current_page") == "opening":
                for direction in frames:
                    if app_state.get("current_page") != "opening":
                        return
                    opening_mark.rotate = ft.Rotate(math.radians(3.8 * direction), alignment=ft.Alignment(0, 0.18))
                    opening_mark.offset = ft.Offset(0.014 * direction, 0)
                    left_pupil.left = left_pupil_base + pupil_shift * direction
                    right_pupil.left = right_pupil_base + pupil_shift * direction
                    page.update()
                    await asyncio.sleep(0.32)

        page.run_task(animate_opening_logo)

    async def start_opening_flow():
        show_opening_page()
        await asyncio.sleep(OPENING_DURATION)
        if is_artist_runtime():
            show_artist_login_page()
        else:
            show_login_page()

    def show_login_page():
        if is_artist_runtime():
            show_artist_login_page()
            return

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
                    "role": "user",
                }
                show_snack(f"{provider}로 로그인하고 있어요.")
                page.run_task(_go_to_home_transition)
            return handler

        def open_signup(e):
            show_signup_page("user")

        def open_artist_login(e):
            show_artist_login_page()

        def themed_login_button(label, bgcolor, text_color, on_click, *, border=None, width=288, delay_ms=0):
            button = ft.Container(
                width=width,
                height=50,
                bgcolor=bgcolor,
                border_radius=17,
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
            padding=ft.padding.only(top=2, bottom=4),
            content=login_logo_visual(156),
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
            padding=ft.padding.symmetric(horizontal=24, vertical=24),
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
                    ft.Container(
                        padding=ft.padding.only(top=4),
                        content=ft.Row(
                            controls=[
                                ft.TextButton(
                                    "회원가입",
                                    style=ft.ButtonStyle(
                                        color=TEXT_COLOR,
                                        text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_700),
                                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    ),
                                    on_click=open_signup,
                                ),
                                *(
                                    [
                                        ft.Text("·", size=11, color=SUBTEXT_COLOR),
                                        ft.TextButton(
                                            "아티스트 로그인하기",
                                            style=ft.ButtonStyle(
                                                color=SUBTEXT_COLOR,
                                                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),
                                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            ),
                                            on_click=open_artist_login,
                                        ),
                                    ]
                                    if is_combined_runtime()
                                    else []
                                ),
                            ],
                            spacing=2,
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                ],
                spacing=11,
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
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
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
                    ),
                ],
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

    def show_signup_page(role="user"):
        if is_artist_runtime():
            role = "artist"
        elif is_customer_runtime() and role == "artist":
            role = "user"

        app_state["current_page"] = "artist_signup" if role == "artist" else "signup"
        is_artist = role == "artist"

        def back_to_login(e=None):
            if is_artist_runtime():
                show_artist_login_page()
            else:
                show_login_page()

        if is_artist:
            title = "아티스트 회원가입"
            subtitle = "소셜 계정으로 빠르게 등록하고 포트폴리오를 준비해요."
            role_label = "아티스트"
        else:
            title = "회원가입"
            subtitle = "소셜 계정으로 가입하고 나에게 맞는 뷰티를 찾아보세요."
            role_label = "이용자"

        provider_user_map = {
            "네이버": ("네이버 회원", "naver"),
            "카카오": ("카카오 회원", "kakao"),
            "구글": ("Google 회원", "google"),
            "애플": ("Apple 회원", "apple"),
        }

        def social_signup(provider):
            def handler(e):
                nickname, provider_key = provider_user_map.get(provider, (f"{provider} 회원", provider))
                if is_artist:
                    nickname = f"{provider} 아티스트"
                app_state["current_user"] = {
                    "provider": f"{'artist_' if is_artist else ''}{provider_key}",
                    "provider_label": f"{role_label} · {provider}",
                    "nickname": nickname,
                    "role": "artist" if is_artist else "user",
                }
                show_snack(f"{provider}로 {role_label} 가입을 진행해요.")
                if is_artist:
                    app_state["artist_approval_status"] = "pending"
                    record_artist_notification(
                        "artist_approval",
                        "아티스트 승인 대기 중",
                        "제출한 정보 확인 후 활동 권한이 열려요.",
                        "artist_approval_pending",
                    )
                    show_artist_approval_pending_page()
                else:
                    show_home_page()
            return handler

        def open_artist_signup(e):
            show_signup_page("artist")

        def signup_button(label, on_click):
            return ft.Container(
                width=288,
                height=50,
                bgcolor="#FFFFFF",
                border_radius=17,
                border=ft.border.all(1, BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=on_click,
                content=ft.Text(label, size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            )

        card = ft.Container(
            width=content_width(),
            height=640,
            padding=ft.padding.symmetric(horizontal=24, vertical=24),
            bgcolor="#FFFFFF",
            border_radius=32,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#0E000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[
                    login_logo_visual(150),
                    ft.Text(title, size=23, weight=ft.FontWeight.W_800, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ft.Text(subtitle, size=11, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=2),
                    signup_button("네이버로 계속하기", social_signup("네이버")),
                    signup_button("카카오로 계속하기", social_signup("카카오")),
                    signup_button("구글로 계속하기", social_signup("구글")),
                    signup_button("애플로 계속하기", social_signup("애플")),
                    ft.Container(
                        visible=(not is_artist and is_combined_runtime()),
                        padding=ft.padding.only(top=4),
                        content=ft.TextButton(
                            "아티스트 회원가입하기",
                            style=ft.ButtonStyle(
                                color=SUBTEXT_COLOR,
                                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                            on_click=open_artist_signup,
                        ),
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        body = ft.Container(
            expand=True,
            bgcolor="#FFFFFF",
            content=ft.Stack(
                controls=[
                    ft.Container(
                        width=full_phone_width(),
                        height=PHONE_HEIGHT,
                        alignment=ft.Alignment(0, 0),
                        content=card,
                    ),
                    ft.Container(
                        left=20,
                        top=22,
                        content=ft.IconButton(
                            icon=app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"),
                            icon_color=TEXT_COLOR,
                            icon_size=20,
                            tooltip="뒤로가기",
                            on_click=back_to_login,
                        ),
                    ),
                ],
            ),
        )

        render_phone_frame(body, None)

    def show_artist_login_page():
        if is_customer_runtime():
            show_login_page()
            return

        app_state["current_page"] = "artist_login"

        def back_to_login(e=None):
            show_login_page()

        def artist_login(provider):
            def handler(e):
                app_state["current_user"] = {
                    "provider": f"artist_{provider}",
                    "provider_label": "아티스트",
                    "nickname": "FINDY 아티스트",
                    "role": "artist",
                }
                app_state["artist_approval_status"] = "approved"
                show_snack("아티스트 계정으로 로그인했어요.")
                show_artist_main_page()
            return handler

        def open_artist_signup(e):
            show_signup_page("artist")

        def artist_login_button(label, on_click):
            return ft.Container(
                width=288,
                height=50,
                bgcolor="#FFFFFF",
                border_radius=17,
                border=ft.border.all(1, BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=on_click,
                content=ft.Text(
                    label,
                    size=15,
                    color=TEXT_COLOR,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
            )

        card = ft.Container(
            width=content_width(),
            height=640,
            padding=ft.padding.symmetric(horizontal=24, vertical=24),
            bgcolor="#FFFFFF",
            border_radius=32,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#0E000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[
                    login_logo_visual(150),
                    ft.Text("아티스트 로그인", size=23, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                    ft.Text("등록된 아티스트 계정으로 FINDY를 관리해보세요.", size=11, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=2),
                    artist_login_button("네이버 아티스트 로그인", artist_login("naver")),
                    artist_login_button("카카오 아티스트 로그인", artist_login("kakao")),
                    artist_login_button("구글 아티스트 로그인", artist_login("google")),
                    artist_login_button("애플 아티스트 로그인", artist_login("apple")),
                    ft.TextButton(
                        "아티스트 회원가입하기",
                        style=ft.ButtonStyle(
                            color=SUBTEXT_COLOR,
                            text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        ),
                        on_click=open_artist_signup,
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        stack_controls = [
            ft.Container(
                width=full_phone_width(),
                height=PHONE_HEIGHT,
                alignment=ft.Alignment(0, 0),
                content=card,
            ),
        ]
        if is_combined_runtime():
            stack_controls.append(
                ft.Container(
                    left=20,
                    top=22,
                    content=ft.IconButton(
                        icon=app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"),
                        icon_color=TEXT_COLOR,
                        icon_size=20,
                        tooltip="뒤로가기",
                        on_click=back_to_login,
                    ),
                )
            )

        body = ft.Container(
            expand=True,
            bgcolor="#FFFFFF",
            content=ft.Stack(
                controls=stack_controls,
            ),
        )

        render_phone_frame(body, None)

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

    def artist_notification_items():
        now_dt = datetime.now()
        notices = list(app_state.get("artist_notifications", []))
        if not notices:
            notices = [
                {
                    "id": "artist_seed_reservation",
                    "kind": "artist_reservation",
                    "title": "새 예약이 체결되었어요",
                    "body": "김수아 · 레이어드컷 상담 · 오늘 11:00",
                    "timestamp": now_dt - timedelta(minutes=18),
                    "target_page": "artist_reservations",
                },
                {
                    "id": "artist_seed_review",
                    "kind": "artist_review",
                    "title": "새 리뷰가 도착했어요",
                    "body": "원하던 분위기를 정확하게 잡아줘서 만족했어요.",
                    "timestamp": now_dt - timedelta(hours=2),
                    "target_page": "artist_reviews",
                },
                {
                    "id": "artist_seed_inquiry",
                    "kind": "message",
                    "title": "고객 메시지가 도착했어요",
                    "body": "예약 전 상담 가능 여부를 확인해주세요.",
                    "timestamp": now_dt - timedelta(hours=5),
                    "target_page": "artist_messages",
                },
            ]
        if app_state.get("artist_approval_status") == "pending":
            notices.insert(
                0,
                {
                    "id": "artist_approval_pending",
                    "kind": "artist_approval",
                    "title": "아티스트 승인 대기 중",
                    "body": "제출한 정보 확인 후 활동 권한이 열려요.",
                    "timestamp": now_dt,
                    "target_page": "artist_approval_pending",
                },
            )
        unique = {}
        for notice in notices:
            unique[notice["id"]] = notice
        return sorted(unique.values(), key=lambda x: x.get("timestamp") or now_dt, reverse=True)

    def current_notification_items():
        if is_artist_runtime() or is_artist_manage_mode():
            return artist_notification_items()
        return reservation_notification_items()

    def unread_notification_count():
        items = current_notification_items()
        read_at = app_state.get("notification_read_at")
        if not read_at:
            return len(items)
        return sum(1 for item in items if item["timestamp"] > read_at)

    def open_notifications_page(e=None):
        close_overlays()
        app_state["notification_read_at"] = datetime.now()
        app_state["selected_tab"] = 4 if (is_artist_runtime() or is_artist_manage_mode()) else 2
        app_state["current_page"] = "notifications"
        show_notification_page()

    def notification_button(size=40, icon_size=20):
        unread_count = unread_notification_count()
        badge_text = "9+" if unread_count > 9 else str(unread_count)
        return ft.Container(
            width=size,
            height=size,
            content=ft.Stack(
                controls=[
                    ft.IconButton(
                        icon=app_icon("NOTIFICATIONS_OUTLINED", "NOTIFICATIONS", "NOTIFICATION_ADD"),
                        icon_color=TEXT_COLOR,
                        icon_size=icon_size,
                        tooltip="알림",
                        on_click=open_notifications_page,
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
        accent = "#B85C5C" if kind == "cancelled" else MAIN_COLOR
        bg = "#FFFFFF" if kind != "cancelled" else "#FFF7F5"
        if kind == "upcoming":
            icon_name = "NOTIFICATIONS_ACTIVE"
        elif kind == "confirmed":
            icon_name = "CHECK_CIRCLE"
        elif kind == "review_request":
            icon_name = "RATE_REVIEW"
        elif kind == "artist_reservation":
            icon_name = "EVENT_AVAILABLE"
        elif kind == "artist_review":
            icon_name = "RATE_REVIEW"
        elif kind in ("artist_inquiry", "message", "artist_message"):
            icon_name = "CHAT_BUBBLE_OUTLINE"
        elif kind == "artist_approval":
            icon_name = "VERIFIED"
        else:
            icon_name = "EVENT_BUSY"

        def open_notice_target(e=None):
            target_page = item.get("target_page")
            if target_page:
                app_state["current_page"] = target_page
                if target_page.startswith("artist_") or target_page == "support":
                    app_state["selected_tab"] = 4
                render_current_page()
            elif kind == "review_request" and item.get("item"):
                if is_artist_manage_mode():
                    show_snack("아티스트 계정에서는 리뷰를 작성할 수 없어요.", bgcolor="#B85C5C")
                    return
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
                bgcolor=BG_COLOR,
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
            open_completion_feedback(
                "문의가 접수되었어요",
                "문의 내역에서 처리 상태를 확인할 수 있어요.",
                "문의 내역 보기",
                "inquiry",
                selected_tab=4,
                icon_name="SUPPORT_AGENT",
            )

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

    def message_thread_card(thread, mode="customer"):
        messages = thread.get("messages") or []
        last_message = messages[-1] if messages else {"text": "아직 메시지가 없어요.", "time": ""}
        title = thread.get("artist_name", "아티스트") if mode == "customer" else thread.get("customer_name", "고객")
        meta = f'{thread.get("category", "메시지")} · {thread.get("updated_at", "")}'
        status = thread.get("status", "진행 중")

        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=lambda e, thread_id=thread.get("id"): open_message_thread(
                thread_id,
                "artist_messages" if mode == "artist" else "customer_messages",
            ),
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=48,
                        height=48,
                        border_radius=16,
                        bgcolor=CHIP_BG,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(app_icon("CHAT_BUBBLE_OUTLINE"), color=MAIN_COLOR, size=24),
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(title, size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_800, expand=True),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        bgcolor=MAIN_COLOR if status == "답장 필요" else CHIP_BG,
                                        border_radius=999,
                                        content=ft.Text(
                                            status,
                                            size=10,
                                            color="#FFFFFF" if status == "답장 필요" else MAIN_COLOR,
                                            weight=ft.FontWeight.W_700,
                                        ),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(meta, size=11, color=SUBTEXT_COLOR),
                            ft.Text(
                                last_message.get("text", ""),
                                size=12,
                                color=SUBTEXT_COLOR,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=5,
                        expand=True,
                    ),
                    ft.Icon(app_icon("CHEVRON_RIGHT"), size=22, color=SUBTEXT_COLOR),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def message_header(title, on_back=None, on_search=None):
        return ft.Row(
            width=content_width(),
            controls=[
                ft.Container(
                    width=52,
                    height=52,
                    border_radius=26,
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, BORDER_COLOR),
                    alignment=ft.Alignment(0, 0),
                    on_click=on_back,
                    ink=True,
                    content=ft.Icon(app_icon("CHEVRON_LEFT", "ARROW_BACK_IOS_NEW"), size=28, color=TEXT_COLOR),
                )
                if on_back
                else ft.Container(width=52),
                ft.Text(title, size=30, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True),
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=24,
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, BORDER_COLOR),
                    alignment=ft.Alignment(0, 0),
                    on_click=on_search,
                    ink=True,
                    content=ft.Icon(app_icon("SEARCH"), size=24, color=MAIN_COLOR),
                )
                if on_search
                else ft.Container(width=48),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def message_artist_search_card(artist):
        existing_thread = find_message_thread_by_artist(artist.get("id"))
        button_label = "채팅 열기" if existing_thread else "채팅 시작"
        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            ink=True,
            on_click=lambda e, item=artist: start_customer_chat_with_artist(item, "message_artist_search"),
            content=ft.Row(
                controls=[
                    ft.Container(width=60, height=60, border_radius=18, bgcolor="#000000"),
                    ft.Column(
                        controls=[
                            ft.Text(artist.get("name", "아티스트"), size=18, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
                            ft.Text(f'{artist.get("category", "뷰티")} · {artist.get("job", "")}', size=12, color=SUBTEXT_COLOR),
                            ft.Text(
                                artist.get("style", artist.get("intro", "")),
                                size=12,
                                color=SUBTEXT_COLOR,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=MAIN_COLOR if not existing_thread else CHIP_BG,
                        border_radius=999,
                        content=ft.Text(
                            button_label,
                            size=11,
                            color="#FFFFFF" if not existing_thread else MAIN_COLOR,
                            weight=ft.FontWeight.W_800,
                        ),
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def show_message_artist_search_page():
        clear_transient_ui()
        close_overlays()
        if is_artist_runtime() or is_artist_manage_mode():
            show_snack("아티스트 모드에서는 고객 메시지를 먼저 작성할 수 없어요.", bgcolor="#B85C5C")
            show_artist_messages_page()
            return

        app_state["selected_tab"] = 5
        app_state["current_page"] = "message_artist_search"
        query_value = app_state.get("message_artist_query", "")

        query_field = ft.TextField(
            width=content_width() - 82,
            value=query_value,
            hint_text="이름, 분야, 스타일을 검색해보세요",
            border_radius=18,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            prefix_icon=app_icon("SEARCH"),
            content_padding=16,
            on_change=lambda e: app_state.__setitem__("message_artist_query", e.control.value or ""),
            on_submit=lambda e: show_message_artist_search_page(),
        )

        def apply_search(e=None):
            app_state["message_artist_query"] = query_field.value or ""
            show_message_artist_search_page()

        query = (query_value or "").strip().lower()

        def matches_artist(artist):
            if not query:
                return True
            fields = [
                artist.get("name", ""),
                artist.get("category", ""),
                artist.get("job", ""),
                artist.get("style", ""),
                artist.get("reason", ""),
                artist.get("intro", ""),
                " ".join(artist.get("tags", [])),
            ]
            return query in " ".join(fields).lower()

        artists = [artist for artist in base_artists if matches_artist(artist)]
        artist_cards = [message_artist_search_card(artist) for artist in artists]
        if not artist_cards:
            artist_cards = [
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=18, vertical=30),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Icon(app_icon("SEARCH"), size=36, color=BORDER_COLOR),
                            ft.Text("검색 결과가 없어요.", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                            ft.Text("다른 이름이나 스타일 키워드로 다시 검색해보세요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ]

        body = ft.Column(
            controls=[
                message_header("아티스트 검색", on_back=lambda e: show_customer_messages_page()),
                ft.Row(
                    width=content_width(),
                    controls=[
                        query_field,
                        ft.Container(
                            width=72,
                            height=54,
                            border_radius=18,
                            bgcolor=MAIN_COLOR,
                            alignment=ft.Alignment(0, 0),
                            on_click=apply_search,
                            ink=True,
                            content=ft.Text("검색", size=13, color="#FFFFFF", weight=ft.FontWeight.W_800),
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                section_title("아티스트", "채팅을 시작할 아티스트를 선택하세요."),
                *artist_cards,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_customer_messages_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 5
        app_state["current_page"] = "customer_messages"
        threads = current_message_threads()

        cards = [message_thread_card(thread, "customer") for thread in threads]
        if not cards:
            cards = [
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=18, vertical=30),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Icon(app_icon("CHAT_BUBBLE_OUTLINE"), size=38, color=BORDER_COLOR),
                            ft.Text("아직 채팅이 없어요.", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Text("오른쪽 상단 검색으로 아티스트를 찾아 채팅을 시작하세요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ]

        body = ft.Column(
            controls=[
                message_header("메시지", on_back=go_back_page, on_search=lambda e: show_message_artist_search_page()),
                ft.Text("예약과 별도로 궁금한 점을 아티스트에게 물어볼 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                *cards,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_artist_messages_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 5
        app_state["current_page"] = "artist_messages"
        threads = current_message_threads()

        cards = [message_thread_card(thread, "artist") for thread in threads]
        if not cards:
            cards = [
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=18, vertical=30),
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Icon(app_icon("CHAT_BUBBLE_OUTLINE"), size=38, color=BORDER_COLOR),
                            ft.Text("새 고객 메시지가 없어요.", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Text("고객이 먼저 보낸 메시지만 이곳에 표시돼요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ]

        body = ft.Column(
            controls=[
                message_header("메시지", on_back=go_back_page),
                ft.Text("고객이 먼저 보낸 메시지에 답장할 수 있어요. 예약 관리는 별도 예약 관리에서 진행해요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                *cards,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_write_artist_message_page():
        clear_transient_ui()
        close_overlays()
        if is_artist_runtime() or is_artist_manage_mode():
            show_snack("아티스트 모드에서는 고객 메시지를 먼저 작성할 수 없어요.", bgcolor="#B85C5C")
            show_artist_messages_page()
            return

        app_state["selected_tab"] = 5
        app_state["current_page"] = "write_artist_message"
        draft = app_state.setdefault("message_draft", {"artist_id": None, "category": "스타일 상담", "content": ""})
        artist = find_artist_by_id(draft.get("artist_id")) or app_state.get("detail_artist") or base_artists[0]
        categories = ["스타일 상담", "가격 문의", "예약 전 상담", "기타"]

        def go_write_back(e=None):
            target = app_state.get("message_back_target")
            if target == "message_artist_search":
                show_message_artist_search_page()
            elif target == "search_results":
                show_search_results_page()
            elif target == "detail":
                show_detail_page()
            else:
                show_customer_messages_page()

        def select_category(category):
            def handler(e):
                draft["category"] = category
                show_write_artist_message_page()
            return handler

        content_field = ft.TextField(
            width=content_width(),
            value=draft.get("content", ""),
            hint_text="궁금한 점을 적어주세요. 예약은 별도 예약 화면에서 진행돼요.",
            multiline=True,
            min_lines=6,
            max_lines=9,
            border_radius=18,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=16,
            on_change=lambda e: draft.__setitem__("content", e.control.value or ""),
        )

        def send_message(e):
            content = (draft.get("content") or "").strip()
            if not content:
                show_snack("메시지 내용을 입력해주세요.", bgcolor="#B85C5C")
                return
            thread = create_customer_message(artist, draft.get("category", "스타일 상담"), content)
            draft["artist_id"] = None
            draft["category"] = "스타일 상담"
            draft["content"] = ""
            app_state["active_message_thread_id"] = thread.get("id")
            app_state["message_back_target"] = "customer_messages"
            show_snack("메시지가 전송되었어요.")
            show_message_detail_page()

        chip_controls = [
            ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=MAIN_COLOR if draft.get("category") == category else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if draft.get("category") == category else BORDER_COLOR),
                on_click=select_category(category),
                ink=True,
                content=ft.Text(
                    category,
                    size=12,
                    color="#FFFFFF" if draft.get("category") == category else TEXT_COLOR,
                    weight=ft.FontWeight.W_700,
                ),
            )
            for category in categories
        ]

        body = ft.Column(
            controls=[
                page_header("메시지 작성", on_back=go_write_back),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(artist.get("name", "아티스트"), size=19, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text(f'{artist.get("category", "헤어")} · {artist.get("job", "")}', size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=6),
                            ft.Text("예약과 메시지는 따로 관리돼요.", size=12, color=MAIN_COLOR, weight=ft.FontWeight.W_700),
                        ],
                        spacing=5,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("메시지 유형", size=13, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Row(controls=chip_controls, wrap=True, spacing=8, run_spacing=8),
                            ft.Container(height=8),
                            ft.Text("메시지 내용", size=13, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            content_field,
                        ],
                        spacing=10,
                    ),
                ),
                soft_button("메시지 보내기", MAIN_COLOR, "white", send_message),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_message_detail_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 5
        app_state["current_page"] = "message_detail"
        thread = find_message_thread(app_state.get("active_message_thread_id"))
        if not thread:
            if is_artist_runtime() or is_artist_manage_mode():
                show_artist_messages_page()
            else:
                show_customer_messages_page()
            return

        is_artist = is_artist_runtime() or is_artist_manage_mode()

        def go_message_back(e=None):
            target = app_state.get("message_back_target")
            if target == "detail":
                show_detail_page()
            elif target == "search_results":
                show_search_results_page()
            elif target == "message_artist_search":
                show_message_artist_search_page()
            elif is_artist or target == "artist_messages":
                show_artist_messages_page()
            else:
                show_customer_messages_page()

        def message_bubble(message):
            own = (is_artist and message.get("sender") == "artist") or ((not is_artist) and message.get("sender") == "customer")
            sender_label = "아티스트" if message.get("sender") == "artist" else thread.get("customer_name", "고객")
            return ft.Row(
                width=content_width(),
                alignment=ft.MainAxisAlignment.END if own else ft.MainAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=int(content_width() * 0.78),
                        padding=ft.padding.symmetric(horizontal=14, vertical=12),
                        bgcolor=MAIN_COLOR if own else "#FFFFFF",
                        border_radius=18,
                        border=ft.border.all(1, MAIN_COLOR if own else BORDER_COLOR),
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    f'{sender_label} · {message.get("time", "")}',
                                    size=10,
                                    color=ft.Colors.with_opacity(0.82, "#FFFFFF") if own else SUBTEXT_COLOR,
                                ),
                                ft.Text(
                                    message.get("text", ""),
                                    size=13,
                                    color="#FFFFFF" if own else TEXT_COLOR,
                                ),
                            ],
                            spacing=6,
                        ),
                    )
                ],
            )

        reply_field = ft.TextField(
            width=content_width(),
            value=app_state.get("message_reply_draft", ""),
            hint_text="고객에게 답장할 내용을 입력해주세요." if is_artist else "추가 메시지를 입력해주세요.",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=18,
            bgcolor="#FFFFFF",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            cursor_color=MAIN_COLOR,
            content_padding=16,
            on_change=lambda e: app_state.__setitem__("message_reply_draft", e.control.value or ""),
        )

        def send_reply(e):
            text = (app_state.get("message_reply_draft") or "").strip()
            if not text:
                show_snack("메시지 내용을 입력해주세요.", bgcolor="#B85C5C")
                return
            append_thread_message(thread, "artist" if is_artist else "customer", text)
            if is_artist:
                snack_text = "고객에게 메시지가 전송되었어요."
            else:
                record_artist_notification(
                    "message",
                    "새 고객 메시지",
                    f'{thread.get("customer_name", "고객")}님이 추가 메시지를 보냈어요.',
                    target_page="artist_messages",
                )
                snack_text = "아티스트에게 메시지가 전송되었어요."
            app_state["message_reply_draft"] = ""
            show_snack(snack_text)
            show_message_detail_page()

        body = ft.Column(
            controls=[
                page_header("메시지 상세", on_back=go_message_back),
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
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                thread.get("customer_name", "고객") if is_artist else thread.get("artist_name", "아티스트"),
                                                size=18,
                                                color=TEXT_COLOR,
                                                weight=ft.FontWeight.W_800,
                                            ),
                                            ft.Text(f'{thread.get("category", "메시지")} · {thread.get("status", "진행 중")}', size=12, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        bgcolor=CHIP_BG,
                                        border_radius=999,
                                        content=ft.Text("예약과 별도", size=10, color=MAIN_COLOR, weight=ft.FontWeight.W_700),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text("이 메시지는 예약 확정이나 변경 요청이 아니며, 단순 상담 메시지로만 관리돼요.", size=11, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Column(controls=[message_bubble(message) for message in thread.get("messages", [])], spacing=10),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("답장" if is_artist else "추가 메시지", size=13, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            reply_field,
                            soft_button("메시지 보내기", MAIN_COLOR, "white", send_reply, width=content_width() - 32),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_notification_page():
        clear_transient_ui()
        close_overlays()
        is_artist_notice = is_artist_runtime() or is_artist_manage_mode()
        app_state["selected_tab"] = 4 if is_artist_notice else 2
        app_state["current_page"] = "notifications"
        app_state["notification_read_at"] = datetime.now()
        items = current_notification_items()
        intro_text = "예약 체결, 리뷰, 메시지 알림을 한곳에서 확인해요." if is_artist_notice else "다가오는 예약과 상태 변경 알림을 모아봤어요."

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
                            ft.Text(intro_text, size=12, color=SUBTEXT_COLOR),
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
        is_artist_home = is_artist_manage_mode()

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
                                ft.Text("검색 결과가 없어요. 다른 키워드로 다시 찾아보세요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
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

        header_logo_path = resolve_asset_file("app_logo/app_findy_logo_wordmark.png")
        header_brand = (
            ft.Image(src=header_logo_path, width=122, height=30, fit=ft.ImageFit.CONTAIN)
            if header_logo_path
            else ft.Text("FINDY", size=28, weight=ft.FontWeight.BOLD, color=MAIN_COLOR)
        )

        header = ft.Container(
            width=content_width(),
            height=64,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            controls=[
                                header_brand,
                                ft.Text("Find Your Beauty", size=13, weight=ft.FontWeight.W_600, color=MAIN_COLOR),
                            ],
                            spacing=2,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(1, 0),
                        content=notification_button(),
                    ),
                ]
            ),
        )

        home_search_submit = submit_artist_content_search if is_artist_home else submit_global_search
        home_search_hint = (
            "스냅, 리뷰, 고객 반응을 검색해보세요"
            if is_artist_home
            else "원하는 무드, 시술, 지역을 검색해보세요"
        )

        global_search_field = ft.TextField(
            width=content_width() - 56,
            height=48,
            value=app_state.get("search_text", ""),
            hint_text=home_search_hint,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.TRANSPARENT,
            cursor_color=MAIN_COLOR,
            text_size=13,
            color=TEXT_COLOR,
            hint_style=ft.TextStyle(color=SUBTEXT_COLOR, size=13),
            content_padding=ft.padding.only(left=16, right=8, top=12, bottom=12),
            on_submit=lambda e: home_search_submit(e.control.value),
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
                        on_click=lambda e: home_search_submit(global_search_field.value),
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

        artist_trend_data = artist_trend_dataset()

        def trend_period_chip(label):
            active = app_state.get("artist_trend_period", "주별") == label

            def handle(e):
                app_state["artist_trend_period"] = label
                show_home_page()

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                bgcolor=MAIN_COLOR if active else CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=handle,
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                ),
            )

        def trend_style_card(item, index):
            return ft.Container(
                width=184,
                padding=ft.padding.symmetric(horizontal=14, vertical=14),
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, BORDER_COLOR),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=14,
                    color="#0A000000",
                    offset=ft.Offset(0, 5),
                ),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=28,
                                    height=28,
                                    border_radius=10,
                                    bgcolor=MAIN_COLOR_SOFT,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(str(index), size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.BOLD),
                                ),
                                ft.Container(expand=True),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=CHIP_BG,
                                    border_radius=999,
                                    content=ft.Text(item["category"], size=9, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(item["title"], size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, max_lines=1),
                        ft.Text(
                            f"검색 {trend_number(item['searches'])} · 좋아요 {item['likes']}",
                            size=10,
                            color=SUBTEXT_COLOR,
                            max_lines=1,
                        ),
                        ft.Text(f"{selected_trend_period} +{item['change']}%", size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                    ],
                    spacing=8,
                ),
            )

        selected_trend_period = app_state.get("artist_trend_period", "주별")
        artist_trend_block = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=16),
            bgcolor=ft.Colors.with_opacity(0.58, "#FFFFFF"),
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=lambda e: show_artist_trend_analysis_page(),
            ink=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color="#0B000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("최근 주목 받는 스타일", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                    ft.Text("고객 검색과 좋아요 흐름을 기준으로 정리했어요.", size=11, color=SUBTEXT_COLOR),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=22, color=MAIN_COLOR),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[trend_period_chip(label) for label in ["일별", "주별", "월별"]],
                        spacing=8,
                        scroll=ft.ScrollMode.HIDDEN,
                    ),
                    ft.Container(
                        width=content_width(),
                        height=132,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Row(
                            controls=[
                                trend_style_card(item, idx)
                                for idx, item in enumerate(artist_trend_data.get(selected_trend_period, []), start=1)
                            ],
                            spacing=10,
                            scroll=ft.ScrollMode.HIDDEN,
                        ),
                    ),
                ],
                spacing=13,
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
        if is_artist_home:
            hero_controls.extend([
                global_search_bar,
                ft.Container(height=12),
                artist_trend_block,
            ])
        else:
            hero_controls.extend([
                global_search_bar,
                ft.Container(height=12),
                search_category_block,
            ])

        hero_block = animated_block(
            ft.Column(
                controls=hero_controls,
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            y=0.03,
        )

        def home_snap_card(item):
            return ft.Container(
                width=108,
                on_click=lambda e: go_snap_page(),
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=108,
                            height=132,
                            border_radius=16,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            bgcolor="#000000",
                            content=ft.Stack(
                                controls=[
                                    ft.Container(expand=True, bgcolor="#000000"),
                                    ft.Container(
                                        left=8,
                                        top=8,
                                        padding=ft.padding.symmetric(horizontal=7, vertical=3),
                                        bgcolor=ft.Colors.with_opacity(0.86, "#FFFFFF"),
                                        border_radius=999,
                                        content=ft.Text(item.get("category", "스냅"), size=8, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                                    ),
                                    ft.Container(
                                        right=8,
                                        bottom=8,
                                        padding=ft.padding.symmetric(horizontal=7, vertical=3),
                                        bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                                        border_radius=999,
                                        content=ft.Text(f"♡ {item.get('likes', 0)}", size=8, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                                    ),
                                ],
                            ),
                        ),
                        ft.Text(item.get("title", "스냅"), size=12, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, max_lines=1),
                    ],
                    spacing=7,
                ),
            )

        def build_home_snap_preview():
            snap_items = []
            for category_name in ["헤어", "네일아트", "메이크업", "웨딩", "포토", "반영구"]:
                snap_items.extend(get_snap_feed_items("recommended", category_name)[:1])
            return ft.Container(
                width=content_width(),
                height=174,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    controls=[home_snap_card(item) for item in snap_items[:6]],
                    spacing=8,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )

        def mini_photo_stack():
            return ft.Row(
                controls=[
                    ft.Container(width=38, height=38, bgcolor="#000000", border_radius=11),
                    ft.Container(width=38, height=38, bgcolor="#000000", border_radius=11),
                    ft.Container(width=38, height=38, bgcolor="#000000", border_radius=11),
                ],
                spacing=5,
            )

        def home_review_preview_card(name, category, review, index):
            return ft.Container(
                width=270,
                height=150,
                padding=ft.padding.symmetric(horizontal=14, vertical=13),
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, BORDER_COLOR),
                on_click=lambda e: show_review_page(),
                ink=True,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=14,
                    color="#0A000000",
                    offset=ft.Offset(0, 5),
                ),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, expand=True),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=CHIP_BG,
                                    border_radius=999,
                                    content=ft.Text(category, size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text("★★★★★", size=12, color="#E6B84A"),
                        ft.Text(review, size=12, color=SUBTEXT_COLOR, max_lines=2),
                        mini_photo_stack(),
                    ],
                    spacing=8,
                ),
            )

        def build_home_review_preview():
            review_items = get_review_items()
            return ft.Container(
                width=content_width(),
                height=162,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    controls=[
                        home_review_preview_card(name, category, review, idx)
                        for idx, (name, category, review) in enumerate(review_items)
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )

        def home_artist_preview_card(artist):
            def open_card(e):
                open_detail(artist, back_target="home")

            return ft.Container(
                width=148,
                height=208,
                padding=10,
                bgcolor="#FFFFFF",
                border_radius=22,
                border=ft.border.all(1, BORDER_COLOR),
                on_click=open_card,
                ink=True,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=16,
                    color="#0E000000",
                    offset=ft.Offset(0, 6),
                ),
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=128,
                            height=92,
                            border_radius=16,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=black_image_box(128, 92),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(artist["name"], size=13, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, max_lines=1),
                                ft.Text(artist["job"], size=11, color=SUBTEXT_COLOR, max_lines=1),
                                ft.Text(f"⭐ {artist['rating']} · {artist['distance']}", size=10, color=SUBTEXT_COLOR, max_lines=1),
                            ],
                            spacing=3,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            bgcolor=CHIP_BG,
                            border_radius=999,
                            content=ft.Text(artist["tags"][0], size=9, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                        ),
                    ],
                    spacing=7,
                ),
            )

        def build_home_artist_preview():
            featured_artists = [artist.copy() for artist in base_artists]
            return ft.Container(
                width=content_width(),
                height=224,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    controls=[home_artist_preview_card(artist) for artist in featured_artists],
                    spacing=10,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )

        snap_block = animated_block(
            ft.Column(
                controls=[
                    section_title("오늘의 스냅", on_click=lambda e: go_snap_page()),
                    build_home_snap_preview(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        review_block = animated_block(
            ft.Column(
                controls=[
                    section_title("실제 리뷰", on_click=lambda e: show_review_page()),
                    build_home_review_preview(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        artist_block = animated_block(
            ft.Column(
                controls=[
                    section_title("추천 아티스트", on_click=lambda e: show_search_page()),
                    build_home_artist_preview(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        animated_sections = [hero_block, snap_block, review_block]
        if not is_artist_home:
            animated_sections.append(artist_block)

        body_controls = [
            hero_block,
            ft.Container(height=16),
            snap_block,
            ft.Container(height=18),
            review_block,
            ft.Container(height=18),
        ]
        if not is_artist_home:
            body_controls.extend([
                artist_block,
                ft.Container(height=18),
            ])

        body = ft.Column(
            controls=body_controls,
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
            bgcolor=CARD_COLOR if active else ft.Colors.TRANSPARENT,
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
            bgcolor=CHIP_BG if active else CARD_COLOR,
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
            bgcolor=CHIP_BG if active else CARD_COLOR,
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

        option_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
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
        wordmark_path = resolve_asset_file("app_logo/app_findy_logo_wordmark.png")
        wordmark_width = 122
        wordmark_height = 30
        intro_height = 32
        wordmark = (
            ft.Container(
                width=wordmark_width,
                height=intro_height,
                alignment=ft.Alignment(0, 0),
                content=ft.Image(src=wordmark_path, width=wordmark_width, height=wordmark_height, fit=ft.ImageFit.CONTAIN),
            )
            if wordmark_path
            else ft.Container(
                width=wordmark_width,
                height=intro_height,
                alignment=ft.Alignment(0, 0),
                content=ft.Text("FINDY", size=23, weight=ft.FontWeight.W_800, color=MAIN_COLOR),
            )
        )
        title_label = ft.Container(
            height=18,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
        )
        return ft.Container(
            width=content_width(),
            content=ft.Stack(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Column(
                                controls=[
                                    wordmark,
                                    title_label,
                                    ft.Text(subtitle, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                                ],
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                margin=ft.margin.only(top=10),
                                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                            ),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        alignment=ft.Alignment(1, -1),
                        content=notification_button(),
                    ),
                ],
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
                            ft.Text("자유롭게 스냅작성", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
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
                    page_header("스냅 작성", on_back=safe_go_back),
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
            open_completion_feedback(
                "스냅이 등록되었어요",
                "작성한 스냅은 스냅 화면에서 확인할 수 있어요.",
                "스냅 보기",
                "snap",
                selected_tab=1,
                icon_name="PHOTO_LIBRARY",
            )

        body = ft.Column(
            controls=[
                page_header("스냅 작성", on_back=safe_go_back),
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

    def show_video_detail_page(video=None):
        if video is not None:
            app_state["video_detail_item"] = video
        video = app_state.get("video_detail_item")
        if not video:
            show_video_page()
            return

        app_state["selected_tab"] = 3
        app_state["current_page"] = "video_detail"
        key = video_key(video)
        liked_ids = app_state.setdefault("video_liked_keys", set())
        saved_ids = app_state.setdefault("video_saved_keys", set())
        comment_count = {"value": int(video.get("comments", 0) or 0)}

        like_label = ft.Text("", size=13, weight=ft.FontWeight.W_700)
        save_label = ft.Text("", size=13, weight=ft.FontWeight.W_700)
        comment_label = ft.Text(f"댓글 {comment_count['value']}", size=13, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700)
        like_button = ft.Container(width=96, height=40, border_radius=999, alignment=ft.Alignment(0, 0))
        save_button = ft.Container(width=96, height=40, border_radius=999, alignment=ft.Alignment(0, 0))
        comment_field = ft.TextField(
            width=content_width(),
            hint_text="댓글을 입력해주세요.",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )

        def refresh_actions():
            liked = key in liked_ids
            saved = key in saved_ids
            like_button.bgcolor = MAIN_COLOR if liked else "#FFFFFF"
            like_button.border = ft.border.all(1, MAIN_COLOR if liked else BORDER_COLOR)
            like_label.value = "좋아요 취소" if liked else "좋아요"
            like_label.color = "#FFFFFF" if liked else SUBTEXT_COLOR
            save_button.bgcolor = MAIN_COLOR_SOFT if saved else "#FFFFFF"
            save_button.border = ft.border.all(1, MAIN_COLOR if saved else BORDER_COLOR)
            save_label.value = "저장됨" if saved else "저장"
            save_label.color = MAIN_COLOR if saved else SUBTEXT_COLOR

        def update_actions():
            for control in [like_button, save_button, like_label, save_label, comment_label]:
                try:
                    control.update()
                except Exception:
                    pass

        def toggle_like(e):
            if key in liked_ids:
                liked_ids.discard(key)
            else:
                liked_ids.add(key)
            refresh_actions()
            update_actions()

        def toggle_save(e):
            if key in saved_ids:
                saved_ids.discard(key)
            else:
                saved_ids.add(key)
            refresh_actions()
            update_actions()

        def submit_comment(e):
            if not (comment_field.value or "").strip():
                show_snack("댓글을 입력해주세요.", bgcolor="#B85C5C")
                return
            comment_count["value"] += 1
            video["comments"] = comment_count["value"]
            comment_label.value = f"댓글 {comment_count['value']}"
            comment_field.value = ""
            comment_label.update()
            comment_field.update()
            show_snack("댓글이 등록되었어요.")

        like_button.on_click = toggle_like
        save_button.on_click = toggle_save
        like_button.ink = True
        save_button.ink = True
        like_button.content = ft.Row(
            controls=[ft.Icon(ft.Icons.FAVORITE_BORDER, size=15, color=SUBTEXT_COLOR), like_label],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        save_button.content = ft.Row(
            controls=[ft.Icon(ft.Icons.BOOKMARK_BORDER, size=15, color=MAIN_COLOR), save_label],
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        refresh_actions()

        body = ft.Column(
            controls=[
                page_header("비디오", on_back=safe_go_back),
                ft.Container(
                    width=content_width(),
                    height=260,
                    border_radius=30,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Stack(
                        controls=[
                            black_image_box(content_width(), 260),
                            ft.Container(alignment=ft.Alignment(0, 0), content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL_ROUNDED, size=66, color=MAIN_COLOR)),
                            ft.Container(
                                right=14,
                                bottom=14,
                                padding=ft.padding.symmetric(horizontal=11, vertical=6),
                                bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                                border_radius=999,
                                content=ft.Text(video.get("duration", "0:00"), size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            ),
                        ]
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
                            ft.Row(
                                controls=[
                                    ft.Text(video.get("title", "비디오"), size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800, expand=True),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                        bgcolor=MAIN_COLOR_SOFT,
                                        border_radius=999,
                                        content=ft.Text(video.get("category", "비디오"), size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                    ),
                                ],
                            ),
                            ft.Text(video.get("subtitle", ""), size=13, color=SUBTEXT_COLOR),
                            ft.Text(f'{video.get("badge", "VIDEO")} · 조회 {video.get("views", "0")}', size=12, color=SUBTEXT_COLOR),
                            ft.Row(controls=[like_button, save_button, ft.Container(width=96, height=40, alignment=ft.Alignment(0, 0), content=comment_label)], spacing=8),
                        ],
                        spacing=12,
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
                            ft.Text("댓글", size=14, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            comment_field,
                            soft_button("댓글 등록", MAIN_COLOR, "white", submit_comment, width=content_width() - 44),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_video_page():
        clear_transient_ui()
        app_state["selected_tab"] = 3
        app_state["current_page"] = "video"

        video_categories = ["전체", "헤어", "메이크업", "네일아트", "웨딩", "포토"]
        selected_cat = app_state.get("video_category_filter", "전체")

        all_videos = get_all_video_items()
        filtered = all_videos if selected_cat == "전체" else [v for v in all_videos if v["category"] == selected_cat]
        if not filtered:
            filtered = all_videos
            selected_cat = "전체"
            app_state["video_category_filter"] = "전체"

        active_index = max(0, min(app_state.get("active_video_index", 0), len(filtered) - 1))
        app_state["active_video_index"] = active_index
        active_video = filtered[active_index]
        active_key = video_key(active_video)
        liked_ids = app_state.setdefault("video_liked_keys", set())
        saved_ids = app_state.setdefault("video_saved_keys", set())

        def choose_cat(cat):
            def handler(e):
                app_state["video_category_filter"] = cat
                app_state["active_video_index"] = 0
                show_video_page()
            return handler

        def move_video(delta):
            def handler(e):
                next_index = active_index + delta
                if next_index < 0 or next_index >= len(filtered):
                    show_snack("표시할 영상이 더 없어요.")
                    return
                app_state["active_video_index"] = next_index
                show_video_page()
            return handler

        def toggle_video_like(e):
            if active_key in liked_ids:
                liked_ids.discard(active_key)
            else:
                liked_ids.add(active_key)
            show_video_page()

        def toggle_video_save(e):
            if active_key in saved_ids:
                saved_ids.discard(active_key)
            else:
                saved_ids.add(active_key)
            show_video_page()

        comment_field = ft.TextField(
            width=content_width(),
            hint_text="댓글을 입력해주세요.",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        comment_count = {"value": int(active_video.get("comments", 0) or 0)}

        def submit_video_comment(e):
            if not (comment_field.value or "").strip():
                show_snack("댓글을 입력해주세요.", bgcolor="#B85C5C")
                return
            comment_count["value"] += 1
            active_video["comments"] = comment_count["value"]
            comment_field.value = ""
            show_snack("댓글이 등록되었어요.")
            show_video_page()

        def video_action_button(icon_name, label, on_click, active=False, width=106):
            return ft.Container(
                width=width,
                height=42,
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                border_radius=999,
                on_click=on_click,
                ink=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=16, color="#FFFFFF" if active else MAIN_COLOR),
                        ft.Text(label, size=13, color="#FFFFFF" if active else MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        cat_chips = ft.Row(
            controls=[
                ft.GestureDetector(
                    on_tap=choose_cat(cat),
                    content=ft.Container(
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        bgcolor=CHIP_BG if cat == selected_cat else CARD_COLOR,
                        border_radius=999,
                        border=ft.border.all(1, MAIN_COLOR if cat == selected_cat else ft.Colors.with_opacity(0.76, BORDER_COLOR)),
                        content=ft.Text(cat, size=12, color=MAIN_COLOR_DARK if cat == selected_cat else TEXT_COLOR, weight=ft.FontWeight.W_600 if cat == selected_cat else ft.FontWeight.NORMAL),
                    ),
                )
                for cat in video_categories
            ],
            spacing=6,
            scroll=ft.ScrollMode.HIDDEN,
        )

        write_video_button = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor=CARD_COLOR,
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

        video_stage_height = 520
        video_stage = ft.Container(
            width=content_width(),
            height=video_stage_height,
            border_radius=34,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor="#000000",
            content=ft.Stack(
                controls=[
                    black_image_box(content_width(), video_stage_height),
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL_ROUNDED, size=74, color=MAIN_COLOR),
                    ),
                    ft.Container(
                        left=18,
                        right=18,
                        bottom=22,
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                            bgcolor=ft.Colors.with_opacity(0.86, "#FFFFFF"),
                                            border_radius=999,
                                            content=ft.Text(active_video.get("category", "비디오"), size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                        ),
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                            bgcolor=ft.Colors.with_opacity(0.86, "#FFFFFF"),
                                            border_radius=999,
                                            content=ft.Text(active_video.get("duration", "0:59"), size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(active_video.get("title", "비디오"), size=21, color="#FFFFFF", weight=ft.FontWeight.W_800),
                                ft.Text(active_video.get("subtitle", ""), size=13, color=ft.Colors.with_opacity(0.84, "#FFFFFF")),
                                ft.Text(f'{active_video.get("badge", "SHORTS")} · 조회 {active_video.get("views", "0")} · 최대 1분', size=12, color=ft.Colors.with_opacity(0.78, "#FFFFFF"), weight=ft.FontWeight.W_600),
                            ],
                            spacing=7,
                        ),
                    ),
                ],
            ),
        )

        video_meta_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"{active_index + 1}/{len(filtered)}", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Container(expand=True),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                bgcolor=MAIN_COLOR_SOFT,
                                border_radius=999,
                                content=ft.Text("1분 이내 영상", size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                            ),
                        ],
                    ),
                    ft.Row(
                        controls=[
                            video_action_button("CHEVRON_LEFT", "이전", move_video(-1), width=86),
                            video_action_button("FAVORITE_BORDER", "좋아요", toggle_video_like, active=active_key in liked_ids),
                            video_action_button("BOOKMARK_BORDER", "저장", toggle_video_save, active=active_key in saved_ids),
                            video_action_button("CHEVRON_RIGHT", "다음", move_video(1), width=86),
                        ],
                        spacing=7,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
            ),
        )

        comment_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("댓글", size=14, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            ft.Container(expand=True),
                            ft.Text(f"{comment_count['value']}개", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                        ],
                    ),
                    comment_field,
                    soft_button("댓글 등록", MAIN_COLOR, "white", submit_video_comment, width=content_width() - 44),
                ],
                spacing=10,
            ),
        )

        body = ft.Column(
            controls=[
                tab_page_intro("비디오", "1분 이내 숏폼 영상으로 스타일 흐름을 바로 확인해요."),
                ft.Container(height=10),
                write_video_button,
                ft.Container(
                    width=content_width(),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=cat_chips,
                ),
                video_stage,
                video_meta_card,
                comment_card,
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

        category_row = ft.Row(spacing=6, scroll=ft.ScrollMode.HIDDEN)
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
            allowed_video_exts = (".mp4", ".mov", ".m4v", ".webm")
            picked_path = str(selected_video_path[0] or "").lower()
            if not picked_path.endswith(allowed_video_exts):
                show_snack("MP4, MOV, M4V, WEBM 영상만 등록할 수 있어요.", bgcolor="#B85C5C")
                return
            if not title:
                show_snack("영상 제목을 입력해주세요.", bgcolor="#B85C5C")
                return
            app_state.setdefault("written_videos", []).insert(0, {
                "title": title,
                "subtitle": subtitle or "업로드한 스타일 영상",
                "badge": "UPLOAD",
                "category": selected_category[0],
                "duration": "0:59",
                "views": "0",
                "video_path": selected_video_path[0],
            })
            app_state["video_category_filter"] = selected_category[0]
            cleanup_file_picker()
            open_completion_feedback(
                "비디오가 등록되었어요",
                "작성한 영상은 비디오 화면에서 확인할 수 있어요.",
                "비디오 보기",
                "video",
                selected_tab=3,
                icon_name="PLAY_CIRCLE",
            )

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
                            ft.Text("MP4, MOV, M4V, WEBM 형식의 1분 이내 영상만 등록할 수 있어요.", size=11, color=SUBTEXT_COLOR),
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
        if is_artist_manage_mode():
            show_snack("아티스트 계정에서는 검색 기능을 사용할 수 없어요.", bgcolor="#B85C5C")
            show_artist_main_page()
            return

        if is_overlay_open("left"):
            app_state["selected_tab"] = 0
        elif is_overlay_open("right"):
            app_state["selected_tab"] = 4
        else:
            app_state["selected_tab"] = 2
        app_state["current_page"] = "search"

        search_logo_path = resolve_asset_file("app_logo/app_findy_logo_horizontal.png")
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
                        content=notification_button(icon_size=22),
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
        logo_width = 188
        logo_height = logo_width * 386 / 760
        pupil_size = logo_width * 0.13
        pupil_y = logo_height * 0.61 - pupil_size / 2
        left_pupil_base = logo_width * 0.317 - pupil_size / 2
        right_pupil_base = logo_width * 0.684 - pupil_size / 2
        pupil_shift = logo_width * 0.035

        shell_path = resolve_asset_file("app_logo/app_findy_logo_mark_shell.png")
        left_pupil = ft.Container(
            left=left_pupil_base,
            top=pupil_y,
            width=pupil_size,
            height=pupil_size,
            bgcolor=LOGO_COLOR,
            border_radius=999,
            animate_position=ft.Animation(240, ft.AnimationCurve.EASE_IN_OUT),
        )
        right_pupil = ft.Container(
            left=right_pupil_base,
            top=pupil_y,
            width=pupil_size,
            height=pupil_size,
            bgcolor=LOGO_COLOR,
            border_radius=999,
            animate_position=ft.Animation(240, ft.AnimationCurve.EASE_IN_OUT),
        )
        search_head = ft.Container(
            width=logo_width,
            height=logo_height,
            alignment=ft.Alignment(0, 0),
            rotate=ft.Rotate(0, alignment=ft.Alignment(0, 0.18)),
            animate_rotation=ft.Animation(260, ft.AnimationCurve.EASE_IN_OUT),
            offset=ft.Offset(0, 0),
            animate_offset=ft.Animation(260, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Stack(
                width=logo_width,
                height=logo_height,
                controls=[
                    ft.Image(
                        src=shell_path or resolve_asset_file("app_logo/app_findy_logo_mark.png"),
                        width=logo_width,
                        height=logo_height,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    left_pupil,
                    right_pupil,
                ],
            ),
        )
        search_visual = ft.Container(
            width=logo_width + 24,
            height=logo_height + 28,
            alignment=ft.Alignment(0, 0),
            content=search_head,
        )

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
                    search_visual,
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
            (0, "주변 아티스트를 탐색 중..."),
            (-1, "스타일 취향을 분석 중..."),
            (1, "지역과 분위기를 매칭 중..."),
            (0, "추천 결과를 정리 중..."),
        ]

        for _ in range(2):
            for direction, msg in frames:
                search_head.rotate = ft.Rotate(math.radians(4 * direction), alignment=ft.Alignment(0, 0.18))
                search_head.offset = ft.Offset(0.018 * direction, 0)
                left_pupil.left = left_pupil_base + pupil_shift * direction
                right_pupil.left = right_pupil_base + pupil_shift * direction
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
        overview_categories = ["전체", "헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
        is_overview_mode = (
            browse_mode
            and app_state.get("selected_category") == "전체"
            and app_state.get("selected_subcategory") in {"아티스트", "샵", "리뷰", "커뮤니티", "카테고리"}
        )
        overview_filter = app_state.get("overview_filter_category", "전체")

        def item_overview_category(item):
            return normalize_overlay_category_name(item.get("category", ""))

        if is_overview_mode and overview_filter != "전체":
            normalized_filter = normalize_overlay_category_name(overview_filter)
            raw_results = [
                item
                for item in raw_results
                if item_overview_category(item) == normalized_filter
            ]

        is_artist_mode = not browse_mode or app_state.get("selected_subcategory") == "아티스트"
        filtered_results = apply_sort_filter(raw_results) if is_artist_mode else raw_results

        def overview_category_chip(label):
            active = overview_filter == label

            def on_tap(e):
                app_state["overview_filter_category"] = label
                show_search_results_page()

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                bgcolor=MAIN_COLOR if active else CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=on_tap,
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                ),
            )

        overview_category_bar = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[overview_category_chip(label) for label in overview_categories],
                spacing=8,
                scroll=ft.ScrollMode.HIDDEN,
            ),
        ) if is_overview_mode else ft.Container()

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
            overview_category_bar,
            ft.Container(height=6 if is_overview_mode else 0),
            filter_bar,
            result_count,
            ft.Container(height=4),
        ]

        if browse_mode and app_state.get("selected_subcategory") == "리뷰" and not is_artist_manage_mode():
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
            if is_artist_mode:
                empty_title = "조건에 맞는 아티스트가 없어요"
                empty_desc = "카테고리나 검색어를 조금 바꿔서 다시 확인해보세요."
            elif browse_mode:
                empty_title = "아직 등록된 목록이 없어요"
                empty_desc = "FINDY에서 확인할 수 있는 콘텐츠를 차근차근 채우고 있어요."
            else:
                empty_title = "조건에 맞는 추천 결과가 없어요"
                empty_desc = "원하는 무드, 시술명, 지역을 조금 다르게 검색해보세요."
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                border_radius=16,
                                bgcolor=CHIP_BG,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon("SEARCH", "EXPLORE"), size=22, color=MAIN_COLOR),
                            ),
                            ft.Text(empty_title, size=16, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text(empty_desc, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
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
                    elif item.get("type") == "beauty_category":
                        cards.append(
                            browse_result_card(
                                item,
                                on_click=lambda e, category=item.get("category", item.get("title")): open_category_recommendations(category, "아티스트"),
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

        def open_category_overview(sub_category):
            app_state["selected_category"] = "전체"
            app_state["selected_subcategory"] = sub_category
            app_state["overview_filter_category"] = "전체"
            app_state["search_text"] = ""
            app_state["search_results"] = build_category_browse_items("전체", sub_category)
            app_state["recommendation_entry"] = f"전체 > {sub_category}"
            app_state["category_browse_mode"] = True
            app_state["search_results_back_target"] = "category"
            app_state["left_menu_expanded"] = None
            app_state["selected_tab"] = 0
            app_state["current_page"] = "search_results"
            show_search_results_page()

        def toggle_category(main_category):
            if app_state.get("left_menu_expanded") == main_category:
                app_state["left_menu_expanded"] = None
            else:
                app_state["left_menu_expanded"] = main_category
            category_list.controls = build_category_cards()
            category_list.update()

        def overview_card(icon_name, title, description, sub_category):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.only(left=16, right=14, top=15, bottom=15),
                border_radius=26,
                bgcolor=CARD_COLOR,
                border=ft.border.all(1, ft.Colors.with_opacity(0.78, BORDER_COLOR)),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=18, color="#0E8B6B4F", offset=ft.Offset(0, 8)),
                on_click=lambda e: open_category_overview(sub_category),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=42,
                                    height=42,
                                    border_radius=16,
                                    bgcolor=CHIP_BG,
                                    border=ft.border.all(1, BORDER_COLOR),
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(app_icon(icon_name), size=20, color=MAIN_COLOR),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(title, size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                                        ft.Text(description, size=11, color=SUBTEXT_COLOR),
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
                            bgcolor=CHIP_BG,
                            border=ft.border.all(1, BORDER_COLOR),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=20, color=MAIN_COLOR),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def category_section_label(title, subtitle):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.only(left=4, top=4, bottom=2),
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                        ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                    ],
                    spacing=2,
                ),
            )

        overview_cards = []
        overview_cards.append(
            overview_card(
                "RATE_REVIEW",
                "리뷰 전체보기",
                "모든 뷰티 카테고리의 리뷰를 한 번에 보기",
                "리뷰",
            )
        )
        overview_cards.append(
            overview_card(
                "FORUM",
                "커뮤니티 전체보기",
                "뷰티 카테고리에 올라온 커뮤니티 글 보기",
                "커뮤니티",
            )
        )
        overview_cards.append(
            overview_card(
                "PERSON_SEARCH",
                "아티스트 전체보기",
                "모든 뷰티 카테고리의 아티스트 보기",
                "아티스트",
            )
        )
        overview_cards.append(
            overview_card(
                "STORE",
                "샵 전체보기",
                "등록된 뷰티 샵을 한 번에 보기",
                "샵",
            )
        )
        beauty_order = ["헤어", "네일아트", "포토", "웨딩", "반영구", "메이크업"]
        category_descriptions = {
            "헤어": "컷, 펌, 컬러와 스타일링",
            "네일아트": "젤, 케어, 디자인 네일",
            "포토": "프로필, 스냅, 콘셉트 촬영",
            "웨딩": "신부, 본식, 리허설 뷰티",
            "반영구": "눈썹, 아이라인, 입술 시술",
            "메이크업": "데일리, 화보, 신부 메이크업",
        }
        def build_category_cards():
            category_cards = []
            for main_category in beauty_order:
                is_expanded = app_state.get("left_menu_expanded") == main_category
                category_cards.append(
                    ft.Container(
                        width=content_width(),
                        padding=ft.padding.only(left=16, right=14, top=15, bottom=15),
                        border_radius=26,
                        bgcolor=CARD_COLOR if not is_expanded else CARD_COLOR,
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
                                            bgcolor=CHIP_BG,
                                            border=ft.border.all(1, BORDER_COLOR),
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
                                    bgcolor=CHIP_BG,
                                    border=ft.border.all(1, BORDER_COLOR),
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
                        category_cards.append(
                            ft.Container(
                                width=content_width() - 28,
                                margin=ft.margin.only(left=14, top=4, bottom=2),
                                padding=ft.padding.symmetric(horizontal=14, vertical=11),
                                border_radius=16,
                                bgcolor=CARD_COLOR,
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
            return category_cards

        category_list = ft.Column(
            controls=build_category_cards(),
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        body = ft.Column(
            controls=[
                tab_page_intro("카테고리", "원하는 항목을 빠르게 탐색해보세요."),
                ft.Container(height=14),
                category_section_label("뷰티 카테고리", "관심 있는 분야를 열어 세부 항목을 둘러보세요."),
                category_list,
                ft.Container(height=8),
                category_section_label("전체보기", "리뷰, 커뮤니티, 아티스트, 샵을 한 번에 확인해요."),
                *overview_cards,
                ft.Container(height=24),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_my_page():
        clear_transient_ui()
        is_artist_account = app_state.get("current_user", {}).get("role") == "artist"
        if is_artist_account:
            show_artist_main_page()
            return
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my"

        controls = [
            tab_page_intro("내정보", "원하는 항목을 빠르게 탐색해보세요."),
            ft.Container(height=14),
            build_my_info_profile_card(),
        ]
        controls.extend([
            ft.Container(height=14),
            build_my_info_menu_section(),
            ft.Container(height=14),
            logout_button(),
            ft.Container(height=24),
        ])

        body = ft.Column(
            controls=controls,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def artist_summary_stat(label, value):
        return ft.Container(
            expand=True,
            padding=ft.padding.symmetric(vertical=12),
            bgcolor=CARD_COLOR,
            border_radius=18,
            border=ft.border.all(1, ft.Colors.with_opacity(0.64, BORDER_COLOR)),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                controls=[
                    ft.Text(label, size=10, color=SUBTEXT_COLOR),
                    ft.Text(str(value), size=17, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def artist_action_card(icon_name, title, subtitle, on_click):
        return ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=16, vertical=15),
            bgcolor=CARD_COLOR,
            border_radius=24,
            border=ft.border.all(1, ft.Colors.with_opacity(0.78, BORDER_COLOR)),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=14, color="#0B8B6B4F", offset=ft.Offset(0, 7)),
            ink=True,
            on_click=on_click,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        border_radius=16,
                        bgcolor=CHIP_BG,
                        border=ft.border.all(1, BORDER_COLOR),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(app_icon(icon_name), size=20, color=MAIN_COLOR),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=15, color=MAIN_COLOR),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def show_artist_main_page(e=None):
        clear_transient_ui()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "artist_main"
        profile = get_artist_profile()
        portfolio_items = get_artist_portfolio_items()
        reviews = [item for item in REVIEW_ITEMS if review_item_category(item) == profile.get("category", "헤어")]
        reservations = upcoming_reservations(limit=3)
        profile_public = bool(profile.get("public", app_state.get("artist_profile_public", True)))
        app_state["artist_profile_public"] = profile_public
        profile["public"] = profile_public

        public_status_text = ft.Text(
            "공개" if profile_public else "비공개",
            size=10,
            color=MAIN_COLOR,
            weight=ft.FontWeight.W_700,
        )

        def toggle_artist_profile_public(e):
            is_public = bool(e.control.value)
            app_state["artist_profile_public"] = is_public
            profile["public"] = is_public
            public_status_text.value = "공개" if is_public else "비공개"
            public_status_text.update()
            show_snack("프로필을 공개로 변경했어요." if is_public else "프로필을 비공개로 변경했어요.")

        public_switch = ft.Switch(
            value=profile_public,
            active_color=MAIN_COLOR,
            on_change=toggle_artist_profile_public,
        )

        profile_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=16, color="#0B000000", offset=ft.Offset(0, 7)),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=56, height=56, border_radius=18, bgcolor="#000000"),
                            ft.Column(
                                controls=[
                                    ft.Text(profile["name"], size=18, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                                    ft.Text(f'{profile["field"]} · {profile["region"]}', size=11, color=SUBTEXT_COLOR),
                                    ft.Text(profile["shop"], size=11, color=SUBTEXT_COLOR),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                bgcolor=MAIN_COLOR_SOFT,
                                border_radius=999,
                                content=public_status_text,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Text(profile["mood"], size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                    ft.Row(
                        controls=[
                            artist_summary_stat("리뷰", len(reviews)),
                            ft.Container(width=8),
                            artist_summary_stat("포트폴리오", len(portfolio_items)),
                            ft.Container(width=8),
                            artist_summary_stat("예약", len(reservations)),
                        ],
                        spacing=0,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("프로필 공개 상태", size=12, color=SUBTEXT_COLOR, expand=True),
                            public_switch,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=12,
            ),
        )

        def artist_section(title, subtitle, controls):
            return ft.Column(
                controls=[
                    ft.Container(
                        width=content_width(),
                        padding=ft.padding.only(left=4, right=4, top=8, bottom=2),
                        content=ft.Column(
                            controls=[
                                ft.Text(title, size=14, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                                ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=4,
                        ),
                    ),
                    *controls,
                ],
                spacing=SPACE_SM,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        completion_items = [
            {
                "label": "주요 정보 컨펌",
                "value": "이름 · 분야 · 지역 · 샵",
                "done": True,
                "action": show_artist_profile_page,
                "note": "회사 컨펌 후 반영",
            },
            {
                "label": "소개와 링크",
                "value": "소개 문구 · 인스타그램",
                "done": bool(profile.get("intro") or profile.get("instagram")),
                "action": show_artist_profile_page,
                "note": "직접 수정 가능",
            },
            {
                "label": "대표 포트폴리오",
                "value": f"{len(portfolio_items)}개 등록",
                "done": bool(portfolio_items),
                "action": show_artist_portfolio_page,
                "note": "사진과 대표작 관리",
            },
            {
                "label": "가격 메뉴",
                "value": "시술명 · 시간 · 가격",
                "done": True,
                "action": show_artist_price_menu_page,
                "note": "예약 전환에 중요",
            },
            {
                "label": "예약 가능 시간",
                "value": "영업시간 · 상담 가능",
                "done": bool(profile.get("hours")),
                "action": show_artist_profile_page,
                "note": "프로필 관리에서 수정",
            },
        ]
        completion_value = sum(1 for item in completion_items if item["done"]) / max(1, len(completion_items))
        completion_open = app_state.get("artist_profile_completion_open", True)

        def completion_row(item):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor="#FFFFFF",
                border_radius=16,
                border=ft.border.all(1, BORDER_COLOR),
                ink=True,
                on_click=lambda e, target=item["action"]: target(),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=30,
                            height=30,
                            border_radius=12,
                            bgcolor=MAIN_COLOR if item["done"] else CHIP_BG,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                app_icon("CHECK", "DONE") if item["done"] else app_icon("EDIT", "MODE_EDIT"),
                                size=15,
                                color="#FFFFFF" if item["done"] else MAIN_COLOR,
                            ),
                        ),
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(item["label"], size=12, weight=ft.FontWeight.W_800, color=TEXT_COLOR, expand=True),
                                        ft.Text(item["note"], size=9, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(item["value"], size=10, color=SUBTEXT_COLOR),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=MAIN_COLOR_DARK),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        completion_body = ft.Column(spacing=10)

        def build_completion_controls():
            is_open = app_state.get("artist_profile_completion_open", True)
            controls = [
                ft.Container(
                    ink=True,
                    on_click=toggle_profile_completion,
                    content=ft.Row(
                        controls=[
                            ft.Text("프로필 완성도", size=14, weight=ft.FontWeight.W_700, color=TEXT_COLOR, expand=True),
                            ft.Text(f"{round(completion_value * 100)}%", size=14, weight=ft.FontWeight.W_800, color=MAIN_COLOR),
                            ft.Icon(
                                app_icon("EXPAND_LESS", "KEYBOARD_ARROW_UP") if is_open else app_icon("EXPAND_MORE", "KEYBOARD_ARROW_DOWN"),
                                size=20,
                                color=MAIN_COLOR_DARK,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.ProgressBar(value=completion_value, color=MAIN_COLOR, bgcolor=MAIN_COLOR_SOFT),
            ]
            if is_open:
                controls.extend(
                    [
                        ft.Text("부족한 항목을 누르면 바로 수정 화면으로 이동해요.", size=11, color=SUBTEXT_COLOR),
                        ft.Column(
                            controls=[completion_row(item) for item in completion_items],
                            spacing=8,
                        ),
                    ]
                )
            return controls

        def toggle_profile_completion(e=None):
            app_state["artist_profile_completion_open"] = not app_state.get("artist_profile_completion_open", True)
            completion_body.controls = build_completion_controls()
            completion_body.update()

        completion_body.controls = build_completion_controls()

        completion = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor=CARD_COLOR,
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=completion_body,
        )

        recent_review = reviews[0] if reviews else None
        recent_review_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            ink=True,
            on_click=lambda e: show_artist_review_manage_page(),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("최근 리뷰 요약", size=14, weight=ft.FontWeight.W_700, color=TEXT_COLOR, expand=True),
                            ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=MAIN_COLOR_DARK),
                        ],
                    ),
                    ft.Text(review_item_body(recent_review, "아직 받은 리뷰가 없어요."), size=12, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text("받은 리뷰와 답글 관리로 이동", size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                ],
                spacing=8,
            ),
        )

        reservation_manage_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=14, color="#08000000", offset=ft.Offset(0, 7)),
            ink=True,
            on_click=lambda e: show_artist_reservation_manage_page(),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=42,
                                height=42,
                                border_radius=16,
                                bgcolor=CHIP_BG,
                                border=ft.border.all(1, BORDER_COLOR),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon("EVENT_NOTE"), size=20, color=MAIN_COLOR),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("예약 관리", size=16, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                                    ft.Text("일정, 요청, 완료와 취소 예약을 한 번에 확인해요.", size=11, color=SUBTEXT_COLOR),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=MAIN_COLOR_DARK),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=1, bgcolor=BORDER_COLOR),
                    ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                content=ft.Column(
                                    controls=[
                                        ft.Text("오늘", size=10, color=SUBTEXT_COLOR),
                                        ft.Text("1건", size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                    ],
                                    spacing=3,
                                ),
                            ),
                            ft.Container(width=1, height=42, bgcolor=BORDER_COLOR),
                            ft.Container(
                                expand=True,
                                content=ft.Column(
                                    controls=[
                                        ft.Text("이번 주", size=10, color=SUBTEXT_COLOR),
                                        ft.Text("3건 예정", size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                    ],
                                    spacing=3,
                                ),
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        bgcolor=CHIP_BG,
                        border_radius=16,
                        content=ft.Text("월간 달력에서 예약 일정과 변경/취소 요청을 바로 관리해요.", size=10, color=SUBTEXT_COLOR),
                    ),
                ],
                spacing=14,
            ),
        )

        artist_profile_section = artist_section(
            "프로필 관리",
            "노출 신뢰도와 예약 전환에 필요한 정보를 관리해요.",
            [
                completion,
                artist_action_card("PERSON_OUTLINE", "프로필 미리보기", "고객에게 보이는 프로필 화면을 확인해요.", lambda e: show_artist_profile_preview_page()),
                artist_action_card("PERSON_OUTLINE", "프로필 관리", "주요 정보는 컨펌 후 반영하고 소개/링크를 관리해요.", lambda e: show_artist_profile_page()),
                artist_action_card("PHOTO_LIBRARY_OUTLINED", "포트폴리오 관리", "사진, 대표작, 태그와 공개 상태를 관리해요.", lambda e: show_artist_portfolio_page()),
                artist_action_card("LIST_ALT", "가격 메뉴 관리", "시술명, 소요 시간, 가격과 예약 가능 여부를 관리해요.", lambda e: show_artist_price_menu_page()),
            ],
        )

        artist_reservation_section = artist_section(
            "예약 관리",
            "고객 예약 일정과 변경/취소 요청을 확인해요.",
            [
                reservation_manage_card,
            ],
        )

        artist_review_section = artist_section(
            "리뷰 관리",
            "받은 리뷰와 답글, 사진 리뷰를 관리해요.",
            [
                recent_review_card,
                artist_action_card("RATE_REVIEW_OUTLINED", "리뷰 관리", "받은 리뷰와 답글을 확인하고 답변해요.", lambda e: show_artist_review_manage_page()),
            ],
        )

        artist_activity_section = ft.Column(
            controls=[
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.only(left=4, right=4, top=4, bottom=2),
                    content=ft.Column(
                        controls=[
                            ft.Text("내 활동", size=14, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("작성한 콘텐츠와 저장한 뷰티를 모아볼 수 있어요.", size=11, color=SUBTEXT_COLOR),
                        ],
                        spacing=4,
                    ),
                ),
                artist_action_card("ADD_PHOTO_ALTERNATE_OUTLINED", "내가 쓴 스냅", "아티스트가 올린 스냅을 확인하고 관리해요.", lambda e: show_my_content_page("스냅")),
                artist_action_card("SMART_DISPLAY_OUTLINED", "내가 쓴 비디오", "업로드한 영상 콘텐츠를 확인해요.", lambda e: show_my_content_page("비디오")),
                artist_action_card("FORUM_OUTLINED", "내가 쓴 커뮤니티", "작성한 커뮤니티 글을 확인해요.", lambda e: show_my_content_page("커뮤니티")),
                artist_action_card("BOOKMARK_BORDER", "저장한 뷰티", "저장한 스냅, 비디오와 참고 자료를 모아봐요.", lambda e: show_saved_page()),
            ],
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        artist_support_section = ft.Column(
            controls=[
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.only(left=4, right=4, top=4, bottom=2),
                    content=ft.Column(
                        controls=[
                            ft.Text("고객 지원", size=14, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("문의와 공지사항을 확인할 수 있어요.", size=11, color=SUBTEXT_COLOR),
                        ],
                        spacing=4,
                    ),
                ),
                artist_action_card("CHAT_BUBBLE_OUTLINE", "고객 메시지", "고객이 보낸 메시지를 확인하고 답장해요.", lambda e: show_artist_messages_page()),
                artist_action_card("SUPPORT_AGENT", "고객센터", "1:1 문의와 문의 내역을 확인해요.", lambda e: show_support_page()),
            ],
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        body = ft.Column(
            controls=[
                tab_page_intro("아티스트", "포트폴리오와 예약을 한 곳에서 관리해보세요."),
                ft.Container(height=14),
                profile_card,
                ft.Container(height=12),
                artist_profile_section,
                artist_reservation_section,
                artist_review_section,
                artist_activity_section,
                artist_support_section,
                logout_button("아티스트 로그아웃", "아티스트 관리 모드에서 나가기"),
                ft.Container(height=24),
            ],
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_artist_profile_preview_page(e=None):
        clear_transient_ui()
        app_state["current_page"] = "artist_profile_preview"
        app_state["selected_tab"] = 4

        profile = get_artist_profile()
        portfolio_items = get_artist_portfolio_items()
        reviews = [
            item for item in REVIEW_ITEMS
            if review_item_category(item) == profile.get("category", "헤어")
        ]
        public = bool(profile.get("public", app_state.get("artist_profile_public", True)))
        mood_tags = [
            tag.strip()
            for tag in str(profile.get("mood", "감성 · 트렌디 · 내추럴")).replace(",", "·").split("·")
            if tag.strip()
        ]
        if not mood_tags:
            mood_tags = ["감성", "트렌디", "내추럴"]

        def profile_stat(value, label):
            return ft.Column(
                controls=[
                    ft.Text(str(value), size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                    ft.Text(label, size=10, color=TEXT_COLOR, weight=ft.FontWeight.W_700, text_align=ft.TextAlign.CENTER),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )

        def mood_chip(label):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                bgcolor=MAIN_COLOR_SOFT,
                border_radius=999,
                content=ft.Text(f"#{label}", size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
            )

        def profile_action(label, action, filled=False):
            return ft.Container(
                expand=True,
                height=40,
                border_radius=RADIUS_MD,
                bgcolor=MAIN_COLOR_DARK if filled else "#FFFFFF",
                border=ft.border.all(1, MAIN_COLOR_DARK if filled else BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=action,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if filled else TEXT_COLOR,
                    weight=ft.FontWeight.W_800,
                    text_align=ft.TextAlign.CENTER,
                ),
            )

        def highlight_item(label, icon_name, action=None):
            return ft.Container(
                width=72,
                ink=True,
                on_click=action or (lambda e: show_snack("준비 중인 항목이에요.")),
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=58,
                            height=58,
                            border_radius=999,
                            border=ft.border.all(2, BORDER_COLOR),
                            bgcolor="#FFFFFF",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon(icon_name), size=24, color=MAIN_COLOR_DARK),
                        ),
                        ft.Text(label, size=10, color=TEXT_COLOR, weight=ft.FontWeight.W_700, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=3,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def tab_button(icon_name, active=False, action=None):
            return ft.Container(
                expand=True,
                height=42,
                alignment=ft.Alignment(0, 0),
                ink=True,
                border=ft.border.only(bottom=ft.BorderSide(2, TEXT_COLOR if active else "#FFFFFF")),
                on_click=action or (lambda e: show_snack("준비 중인 보기 방식이에요.")),
                content=ft.Icon(app_icon(icon_name), size=22, color=TEXT_COLOR if active else SUBTEXT_COLOR),
            )

        def open_portfolio_post(index):
            app_state["artist_profile_post_index"] = index
            show_artist_profile_post_page()

        def portfolio_tile(item, index, tile_size):
            views = item.get("views") or f"{max(8, (index + 1) * 13)}"
            return ft.Container(
                width=tile_size,
                height=tile_size,
                bgcolor="#FFFFFF",
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ink=True,
                on_click=lambda e, i=index: open_portfolio_post(i),
                content=ft.Stack(
                    controls=[
                        black_image_box(tile_size, tile_size, 0),
                        ft.Container(
                            right=6,
                            top=6,
                            padding=ft.padding.all(4),
                            border_radius=999,
                            bgcolor="#CC000000",
                            content=ft.Icon(app_icon("FILTER_NONE"), size=12, color="#FFFFFF"),
                        ),
                        ft.Container(
                            left=6,
                            bottom=6,
                            padding=ft.padding.symmetric(horizontal=6, vertical=3),
                            border_radius=999,
                            bgcolor="#CC000000",
                            content=ft.Row(
                                controls=[
                                    ft.Icon(app_icon("VISIBILITY_OUTLINED"), size=11, color="#FFFFFF"),
                                    ft.Text(str(views), size=10, color="#FFFFFF", weight=ft.FontWeight.W_800),
                                ],
                                spacing=3,
                            ),
                        ),
                    ],
                ),
            )

        def review_preview_card(item):
            name = review_item_name(item)
            body = review_item_body(item, "원하던 분위기를 정확하게 잡아줘서 만족했어요.")
            category = review_item_category(item, profile.get("category", "헤어"))
            return ft.Container(
                width=content_width(),
                padding=SPACE_MD,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=38,
                                    height=38,
                                    border_radius=999,
                                    bgcolor=CHIP_BG,
                                    border=ft.border.all(1, BORDER_COLOR),
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(name[:1], size=14, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(name, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text(category, size=10, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Text("★★★★★", size=11, color="#E5B34F", weight=ft.FontWeight.W_700),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(body, size=12, color=SUBTEXT_COLOR, height=1.45, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                    spacing=10,
                ),
                ink=True,
                on_click=lambda e: show_artist_review_manage_page(),
            )

        tile_size = max(88, int((content_width() - 4) / 3))
        portfolio_grid_rows = []
        preview_items = portfolio_items[:9]
        for index in range(0, len(preview_items), 3):
            row_items = preview_items[index:index + 3]
            row_controls = [portfolio_tile(item, index + offset, tile_size) for offset, item in enumerate(row_items)]
            while len(row_controls) < 3:
                row_controls.append(ft.Container(width=tile_size, height=tile_size, opacity=0))
            portfolio_grid_rows.append(
                ft.Row(
                    width=content_width(),
                    controls=row_controls,
                    spacing=2,
                    alignment=ft.MainAxisAlignment.START,
                )
            )

        portfolio_section_controls = portfolio_grid_rows or [
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                bgcolor="#FFFFFF",
                content=ft.Column(
                    controls=[
                        ft.Icon(app_icon("PHOTO_LIBRARY_OUTLINED"), size=28, color=BORDER_COLOR),
                        ft.Text("아직 공개 포트폴리오가 없어요", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                        ft.Text("포트폴리오 관리에서 대표 작업을 추가해보세요.", size=11, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        ]

        body = ft.Column(
            controls=[
                page_header("아티스트 프로필", on_back=safe_go_back),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_MD,
                    bgcolor="#FFFFFF",
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=86,
                                        content=ft.Column(
                                            controls=[
                                                ft.Container(
                                                    width=78,
                                                    height=78,
                                                    border_radius=999,
                                                    border=ft.border.all(1, BORDER_COLOR),
                                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                                    content=black_image_box(78, 78, 999),
                                                ),
                                                ft.Container(
                                                    width=30,
                                                    height=30,
                                                    margin=ft.margin.only(left=52, top=-30),
                                                    border_radius=999,
                                                    bgcolor=TEXT_COLOR,
                                                    border=ft.border.all(2, "#FFFFFF"),
                                                    alignment=ft.Alignment(0, 0),
                                                    content=ft.Icon(app_icon("ADD"), size=18, color="#FFFFFF"),
                                                ),
                                            ],
                                            spacing=0,
                                        ),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(profile.get("name", "OO 아티스트"), size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                            ft.Row(
                                                controls=[
                                                    profile_stat(len(portfolio_items), "게시물"),
                                                    profile_stat(len(reviews), "리뷰"),
                                                    profile_stat(max(0, len(portfolio_items) * 37 + len(reviews) * 6), "저장"),
                                                ],
                                                spacing=8,
                                            ),
                                        ],
                                        spacing=10,
                                        expand=True,
                                    ),
                                ],
                                spacing=16,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(profile.get("shop", "OO 샵"), size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                    ft.Text(
                                        f'{profile.get("field", "헤어 디자이너")} · {profile.get("region", "강남")}',
                                        size=11,
                                        color=SUBTEXT_COLOR,
                                    ),
                                    ft.Text(profile.get("career", "분위기에 맞는 스타일을 제안해요."), size=12, color=TEXT_COLOR, height=1.35),
                                    ft.Text(profile.get("instagram", "@findy_artist"), size=12, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                    ft.Row(controls=[mood_chip(tag) for tag in mood_tags[:4]], spacing=6, wrap=True),
                                ],
                                spacing=5,
                            ),
                            ft.Row(
                                controls=[
                                    profile_action("프로필 편집", lambda e: show_artist_profile_page()),
                                    profile_action("프로필 공유", lambda e: show_snack("프로필 공유 링크가 복사됐어요.")),
                                ],
                                spacing=10,
                            ),
                            ft.Row(
                                controls=[
                                    highlight_item("New", "ADD", lambda e: show_artist_portfolio_add_page()),
                                    highlight_item("대표", "STAR_OUTLINE", lambda e: show_artist_portfolio_page()),
                                    highlight_item("리뷰", "RATE_REVIEW_OUTLINED", lambda e: show_artist_review_manage_page()),
                                ],
                                spacing=12,
                            ),
                            ft.Row(
                                width=content_width(),
                                controls=[
                                    tab_button("GRID_VIEW", active=True),
                                    tab_button("SMART_DISPLAY_OUTLINED"),
                                    tab_button("AUTORENEW"),
                                    tab_button("PERSON_OUTLINE"),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=16,
                    ),
                ),
                *portfolio_section_controls,
                section_title("최근 리뷰", "프로필에서 보이는 고객 반응이에요.", on_click=lambda e: show_artist_review_manage_page()),
                *(review_preview_card(item) for item in reviews[:3]),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_artist_profile_post_page(e=None):
        clear_transient_ui()
        app_state["current_page"] = "artist_profile_post"
        app_state["selected_tab"] = 4

        profile = get_artist_profile()
        items = get_artist_portfolio_items()
        if not items:
            items = [
                {
                    "id": "sample-portfolio",
                    "title": "레이어드컷 + 볼륨펌",
                    "category": profile.get("category", "헤어"),
                    "style": "감성",
                    "price": "12만원대",
                    "description": "자연스럽게 흐르는 층과 부드러운 볼륨을 살린 스타일",
                }
            ]

        index = int(app_state.get("artist_profile_post_index", 0) or 0)
        index = max(0, min(index, len(items) - 1))
        item = items[index]
        post_key = str(item.get("id") or item.get("title") or index)
        liked_key = f"artist_profile_post_liked_{post_key}"
        saved_key = f"artist_profile_post_saved_{post_key}"
        comments_key = f"artist_profile_post_comments_{post_key}"
        comments = app_state.setdefault(comments_key, ["자연스럽게 이어지는 컬러 흐름이 예뻐요."])

        def post_action(icon_name, label, active, action):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                border_radius=999,
                ink=True,
                on_click=action,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=22, color=MAIN_COLOR_DARK if active else TEXT_COLOR),
                        ft.Text(label, size=11, color=MAIN_COLOR_DARK if active else TEXT_COLOR, weight=ft.FontWeight.W_800),
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def toggle_like(e):
            app_state[liked_key] = not bool(app_state.get(liked_key, False))
            show_artist_profile_post_page()

        def toggle_save(e):
            app_state[saved_key] = not bool(app_state.get(saved_key, False))
            show_artist_profile_post_page()

        def open_other_post(target_index):
            app_state["artist_profile_post_index"] = target_index
            show_artist_profile_post_page()

        comment_field = ft.TextField(
            hint_text="댓글을 입력해주세요.",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR_DARK,
            border_radius=RADIUS_MD,
            text_size=12,
            color=TEXT_COLOR,
            hint_style=ft.TextStyle(size=12, color=SUBTEXT_COLOR),
            multiline=False,
            expand=True,
        )

        def submit_comment(e):
            text = (comment_field.value or "").strip()
            if not text:
                show_snack("댓글을 입력해주세요.")
                return
            comments.append(text)
            show_artist_profile_post_page()

        other_tiles = []
        for tile_index, tile_item in enumerate(items[:6]):
            other_tiles.append(
                ft.Container(
                    width=78,
                    height=78,
                    border_radius=RADIUS_SM,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ink=True,
                    on_click=lambda e, i=tile_index: open_other_post(i),
                    border=ft.border.all(2 if tile_index == index else 0, MAIN_COLOR_DARK if tile_index == index else "#FFFFFF"),
                    content=black_image_box(78, 78, RADIUS_SM),
                )
            )

        body = ft.Column(
            controls=[
                page_header("게시물", on_back=lambda e: show_artist_profile_preview_page()),
                ft.Container(
                    width=content_width(),
                    bgcolor="#FFFFFF",
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=40,
                                        height=40,
                                        border_radius=999,
                                        border=ft.border.all(1, BORDER_COLOR),
                                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                        content=black_image_box(40, 40, 999),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(profile.get("name", "OO 아티스트"), size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                            ft.Text(profile.get("shop", "OO 샵"), size=10, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    ft.Icon(app_icon("MORE_HORIZ"), size=22, color=TEXT_COLOR),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                width=content_width(),
                                height=min(430, int(content_width() * 1.18)),
                                border_radius=RADIUS_MD,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Stack(
                                    controls=[
                                        black_image_box(content_width(), min(430, int(content_width() * 1.18)), RADIUS_MD),
                                        ft.Container(
                                            right=12,
                                            top=12,
                                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                            border_radius=999,
                                            bgcolor="#AA000000",
                                            content=ft.Text("1/3", size=12, color="#FFFFFF", weight=ft.FontWeight.W_800),
                                        ),
                                    ],
                                ),
                            ),
                            ft.Row(
                                controls=[
                                    post_action("FAVORITE" if app_state.get(liked_key) else "FAVORITE_BORDER", "좋아요", bool(app_state.get(liked_key)), toggle_like),
                                    post_action("CHAT_BUBBLE_OUTLINE", f"댓글 {len(comments)}", False, lambda e: None),
                                    post_action("SEND_OUTLINED", "공유", False, lambda e: show_snack("게시물 공유 링크가 복사됐어요.")),
                                    ft.Container(expand=True),
                                    post_action("BOOKMARK" if app_state.get(saved_key) else "BOOKMARK_BORDER", "저장", bool(app_state.get(saved_key)), toggle_save),
                                ],
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(item.get("title") or item.get("name") or "포트폴리오", size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                    ft.Text(
                                        f'{item.get("category", profile.get("category", "헤어"))} · {item.get("style", "감성")} · {item.get("price", "상담 후 안내")}',
                                        size=12,
                                        color=MAIN_COLOR_DARK,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    ft.Text(item.get("description", "고객 분위기에 맞춰 자연스럽게 완성한 스타일입니다."), size=13, color=TEXT_COLOR, height=1.45),
                                ],
                                spacing=6,
                            ),
                            ft.Container(height=1, bgcolor=BORDER_COLOR),
                            ft.Column(
                                controls=[
                                    ft.Text("댓글", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                    *[
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    width=28,
                                                    height=28,
                                                    border_radius=999,
                                                    bgcolor=CHIP_BG,
                                                    alignment=ft.Alignment(0, 0),
                                                    content=ft.Text("고", size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                                ),
                                                ft.Text(comment, size=12, color=TEXT_COLOR, expand=True),
                                            ],
                                            spacing=8,
                                        )
                                        for comment in comments[-3:]
                                    ],
                                    ft.Row(
                                        controls=[
                                            comment_field,
                                            ft.Container(
                                                width=62,
                                                height=48,
                                                border_radius=RADIUS_MD,
                                                bgcolor=MAIN_COLOR_DARK,
                                                alignment=ft.Alignment(0, 0),
                                                ink=True,
                                                on_click=submit_comment,
                                                content=ft.Text("등록", size=12, color="#FFFFFF", weight=ft.FontWeight.W_800),
                                            ),
                                        ],
                                        spacing=8,
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.Container(
                                visible=bool(other_tiles),
                                content=ft.Column(
                                    controls=[
                                        ft.Text("다른 포트폴리오", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Row(controls=other_tiles, spacing=6, scroll=ft.ScrollMode.HIDDEN),
                                    ],
                                    spacing=10,
                                ),
                            ),
                        ],
                        spacing=14,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_artist_trend_analysis_page(e=None):
        clear_transient_ui()
        app_state["selected_tab"] = 2
        app_state["current_page"] = "artist_trend_analysis"

        periods = ["일별", "주별", "월별"]
        categories = ["전체", "헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
        selected_period = app_state.get("artist_trend_period", "주별")
        selected_category = app_state.get("artist_trend_category", "헤어")
        detail_items = artist_trend_items(selected_period, selected_category)
        chart_items = detail_items

        def analysis_period_chip(label):
            active = selected_period == label

            def handle(e):
                app_state["artist_trend_period"] = label
                show_artist_trend_analysis_page()

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                bgcolor=MAIN_COLOR if active else CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=handle,
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                ),
            )

        def analysis_category_chip(label):
            active = selected_category == label

            def handle(e):
                app_state["artist_trend_category"] = label
                show_artist_trend_analysis_page()

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=handle,
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                ),
            )

        def metric_card(label, value, subtext):
            return ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=13),
                bgcolor=CARD_COLOR,
                border_radius=18,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text(label, size=10, color=SUBTEXT_COLOR),
                        ft.Text(value, size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Text(subtext, size=9, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                    ],
                    spacing=4,
                ),
            )

        detail_searches = sum(item["searches"] for item in detail_items)
        detail_likes = sum(item["likes"] for item in detail_items)
        detail_saves = sum(item["saves"] for item in detail_items)
        avg_change = round(sum(item["change"] for item in detail_items) / max(len(detail_items), 1))
        max_searches = max([item["searches"] for item in chart_items] or [1])
        top_item = detail_items[0] if detail_items else {"title": "트렌드", "category": selected_category, "keywords": [], "change": 0, "searches": 1, "likes": 0, "saves": 0}
        fast_rising_item = max(detail_items, key=lambda item: item.get("change", 0), default=top_item)
        high_reaction_item = max(
            detail_items,
            key=lambda item: (item.get("likes", 0) + item.get("saves", 0)) / max(item.get("searches", 1), 1),
            default=top_item,
        )
        save_rate = round((detail_saves / max(detail_searches, 1)) * 100, 1)
        reaction_rate = round(((detail_likes + detail_saves) / max(detail_searches, 1)) * 100, 1)
        category_label = selected_category if selected_category != "전체" else "전체 카테고리"

        keyword_counts = {}
        for item in detail_items:
            for keyword in item.get("keywords", []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        top_keywords = [
            keyword
            for keyword, _ in sorted(keyword_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:6]
        ]

        def bar_row(item, index):
            ratio = max(0.08, item["searches"] / max_searches)
            leading_label = item["category"] if selected_category == "전체" else f"{index}위"
            return ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(leading_label, size=11, color=SUBTEXT_COLOR, width=52),
                            ft.Text(item["title"], size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_600, expand=True, max_lines=1),
                            ft.Text(f"+{item['change']}%", size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Stack(
                        controls=[
                            ft.Container(height=10, bgcolor=MAIN_COLOR_SOFT, border_radius=999),
                            ft.Container(width=(content_width() - 88) * ratio, height=10, bgcolor=MAIN_COLOR, border_radius=999),
                        ],
                    ),
                    ft.Text(
                        f"검색 {trend_number(item['searches'])} · 좋아요 {item['likes']} · 저장 {item['saves']}",
                        size=10,
                        color=SUBTEXT_COLOR,
                    ),
                ],
                spacing=5,
            )

        def line_graph_visual():
            graph_width = max(288, content_width() - 48)
            graph_height = 190
            plot_top = 20
            plot_height = 116
            label_top = plot_top + plot_height + 18
            plot_left = 34
            plot_right = 34
            items = chart_items[:6]
            if not items:
                return ft.Container(height=graph_height)

            point_count = len(items)
            plot_width = max(80, graph_width - plot_left - plot_right)
            step = plot_width / max(point_count - 1, 1)
            points = []
            for index, item in enumerate(items):
                ratio = item["searches"] / max_searches if max_searches else 0
                x = plot_left + (step * index if point_count > 1 else plot_width / 2)
                y = plot_top + (1 - ratio) * plot_height
                points.append((x, y, item))

            def safe_left(center_x, width):
                return max(0, min(graph_width - width, center_x - (width / 2)))

            graph_controls = []
            for guide_index in range(3):
                guide_y = plot_top + (plot_height / 2) * guide_index
                graph_controls.append(
                    ft.Container(
                        left=plot_left,
                        top=guide_y,
                        width=plot_width,
                        height=1,
                        bgcolor=MAIN_COLOR_SOFT,
                    )
                )

            for start, end in zip(points, points[1:]):
                x1, y1, _ = start
                x2, y2, _ = end
                line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                line_angle = math.atan2(y2 - y1, x2 - x1)
                graph_controls.append(
                    ft.Container(
                        left=x1,
                        top=y1,
                        width=line_length,
                        height=3,
                        bgcolor=MAIN_COLOR,
                        border_radius=999,
                        rotate=ft.Rotate(angle=line_angle, alignment=ft.Alignment(-1, 0)),
                    )
                )

            for x, y, item in points:
                label = item["category"] if selected_category == "전체" else item["title"]
                graph_controls.extend(
                    [
                        ft.Container(
                            left=safe_left(x, 18),
                            top=y - 8,
                            width=18,
                            height=18,
                            bgcolor="#FFFFFF",
                            border_radius=999,
                            border=ft.border.all(3, MAIN_COLOR),
                        ),
                        ft.Container(
                            left=safe_left(x, 58),
                            top=max(0, y - 34),
                            width=58,
                            content=ft.Text(
                                trend_number(item["searches"]),
                                size=9,
                                color=MAIN_COLOR_DARK,
                                weight=ft.FontWeight.W_700,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ),
                        ft.Container(
                            left=safe_left(x, 70),
                            top=label_top,
                            width=70,
                            content=ft.Text(
                                label,
                                size=9,
                                color=TEXT_COLOR,
                                weight=ft.FontWeight.W_600,
                                text_align=ft.TextAlign.CENTER,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                    ]
                )

            return ft.Container(
                height=graph_height,
                padding=ft.padding.only(top=4),
                content=ft.Stack(controls=graph_controls, width=graph_width, height=graph_height),
            )

        def graph_summary_chip(item, index):
            label = item["category"] if selected_category == "전체" else item["title"]
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=7),
                bgcolor=MAIN_COLOR_SOFT if index == 1 else CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Text(
                    f"{index}위 {label}",
                    size=10,
                    color=MAIN_COLOR_DARK if index == 1 else TEXT_COLOR,
                    weight=ft.FontWeight.W_700 if index == 1 else ft.FontWeight.W_600,
                ),
            )

        def keyword_chip(label):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                bgcolor=CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Text(label, size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
            )

        def insight_card(title, subtitle, icon_name, child_controls):
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_XL,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(title, size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text(subtitle, size=10, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Container(
                                    width=34,
                                    height=34,
                                    border_radius=14,
                                    bgcolor=MAIN_COLOR_SOFT,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(app_icon(icon_name), size=18, color=MAIN_COLOR),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        *child_controls,
                    ],
                    spacing=13,
                ),
            )

        def insight_line(label, value, note):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=CARD_COLOR,
                border_radius=16,
                border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                content=ft.Row(
                    controls=[
                        ft.Text(label, size=11, color=SUBTEXT_COLOR, width=72),
                        ft.Column(
                            controls=[
                                ft.Text(value, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                ft.Text(note, size=10, color=SUBTEXT_COLOR),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def style_detail_card(item, index):
            upload_hint = "전후 사진 + 가까운 디테일 컷" if index == 1 else "시술 과정 또는 결과 비교 이미지"
            keyword_text = ", ".join(item.get("keywords", [])[:2]) or "대표 키워드"
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
                                ft.Container(
                                    width=32,
                                    height=32,
                                    border_radius=11,
                                    bgcolor=MAIN_COLOR_SOFT,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text(str(index), size=12, color=MAIN_COLOR_DARK, weight=ft.FontWeight.BOLD),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(item["title"], size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text(f"{item['category']} · 검색 {trend_number(item['searches'])}", size=11, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Text(f"+{item['change']}%", size=13, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text("함께 검색된 키워드", size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                        ft.Row(
                            controls=[
                                keyword_chip(keyword)
                                for keyword in item.get("keywords", [])[:3]
                            ],
                            spacing=6,
                            scroll=ft.ScrollMode.HIDDEN,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=10),
                            bgcolor=CARD_COLOR,
                            border_radius=16,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                            content=ft.Column(
                                controls=[
                                    ft.Text("추천 활용", size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                                    ft.Text(
                                        f"{upload_hint}에 '{keyword_text}' 태그를 함께 넣어보세요.",
                                        size=11,
                                        color=TEXT_COLOR,
                                    ),
                                ],
                                spacing=3,
                            ),
                        ),
                    ],
                    spacing=12,
                ),
            )

        overview_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=16, color="#0B000000", offset=ft.Offset(0, 7)),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            metric_card("총 검색", trend_number(detail_searches), f"{selected_period} 기준"),
                            ft.Container(width=8),
                            metric_card("저장률", f"{save_rate}%", "관심 유지"),
                            ft.Container(width=8),
                            metric_card("상승폭", f"+{avg_change}%", "평균 변화"),
                        ],
                        spacing=0,
                    ),
                    ft.Text(
                        f"{selected_period} {category_label}에서는 '{top_item['title']}' 수요가 가장 높고, '{fast_rising_item['title']}'의 상승 흐름이 눈에 띄어요.",
                        size=11,
                        color=SUBTEXT_COLOR,
                    ),
                ],
                spacing=12,
            ),
        )

        visual_graph_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "카테고리 검색량 그래프" if selected_category == "전체" else f"{selected_category} 스타일 검색량 그래프",
                                        size=16,
                                        color=TEXT_COLOR,
                                        weight=ft.FontWeight.W_800,
                                    ),
                                    ft.Text(
                                        "점과 선으로 고객 검색 수요의 흐름을 한눈에 보여줘요.",
                                        size=10,
                                        color=SUBTEXT_COLOR,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=22, color=MAIN_COLOR),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    line_graph_visual(),
                    ft.Row(
                        controls=[
                            graph_summary_chip(item, idx)
                            for idx, item in enumerate(chart_items[:3], start=1)
                        ],
                        spacing=7,
                        scroll=ft.ScrollMode.HIDDEN,
                    ),
                ],
                spacing=10,
            ),
        )

        keyword_analysis_card = insight_card(
            "함께 검색된 키워드",
            "대표 스타일과 함께 자주 등장한 단어예요.",
            "SELL_OUTLINED",
            [
                ft.Row(
                    controls=[keyword_chip(keyword) for keyword in top_keywords],
                    spacing=6,
                    wrap=True,
                ),
                insight_line(
                    "활용법",
                    f"{top_item['title']} + {', '.join(top_item.get('keywords', [])[:2]) or '대표 키워드'}",
                    "포트폴리오 제목, 설명, 태그에 함께 넣으면 검색 맥락이 선명해져요.",
                ),
            ],
        )

        reaction_analysis_card = insight_card(
            "고객 반응 분석",
            "좋아요와 저장 흐름으로 실제 관심도를 봐요.",
            "FAVORITE_BORDER",
            [
                insight_line(
                    "반응률",
                    f"{reaction_rate}%",
                    f"검색 대비 좋아요와 저장이 이어진 비율이에요. 저장 {detail_saves}개",
                ),
                insight_line(
                    "저장 강세",
                    high_reaction_item["title"],
                    f"검색 대비 저장/좋아요 반응이 좋아요. +{high_reaction_item['change']}%",
                ),
                insight_line(
                    "상승 주목",
                    fast_rising_item["title"],
                    f"최근 변화폭이 가장 커요. 이번 기간 +{fast_rising_item['change']}%",
                ),
            ],
        )

        portfolio_action_card = insight_card(
            "포트폴리오 추천 액션",
            "지금 올리면 좋은 콘텐츠 방향을 제안해요.",
            "TIPS_AND_UPDATES_OUTLINED",
            [
                insight_line(
                    "1순위",
                    f"{top_item['title']} 결과 컷 업로드",
                    "첫 사진은 완성 컷, 다음 사진은 디테일/전후 비교로 구성해보세요.",
                ),
                insight_line(
                    "태그",
                    " · ".join(top_item.get("keywords", [])[:3]) or category_label,
                    "고객이 같이 검색한 단어를 태그로 쓰면 발견 가능성이 높아져요.",
                ),
                insight_line(
                    "설명",
                    f"{category_label} 고객에게 어울리는 무드와 유지 팁을 짧게 작성",
                    "단순 예쁜 사진보다 상담 전에 확인할 정보가 있는 콘텐츠가 저장으로 이어져요.",
                ),
            ],
        )

        controls = [
            page_header("트렌드 분석", on_back=safe_go_back),
            ft.Container(
                width=content_width(),
                content=ft.Text(
                    "고객이 많이 검색하고 저장한 스타일을 카테고리별로 확인해요.",
                    size=12,
                    color=SUBTEXT_COLOR,
                ),
            ),
            ft.Row(
                controls=[analysis_period_chip(label) for label in periods],
                spacing=8,
                scroll=ft.ScrollMode.HIDDEN,
            ),
            ft.Row(
                controls=[analysis_category_chip(label) for label in categories],
                spacing=8,
                scroll=ft.ScrollMode.HIDDEN,
            ),
            overview_card,
            visual_graph_card,
            keyword_analysis_card,
            reaction_analysis_card,
            portfolio_action_card,
            ft.Container(
                width=content_width(),
                content=ft.Text(
                    f"{selected_category} 상세 랭킹" if selected_category != "전체" else "전체 상세 랭킹",
                    size=16,
                    color=TEXT_COLOR,
                    weight=ft.FontWeight.W_800,
                ),
            ),
        ]
        controls.extend([style_detail_card(item, idx) for idx, item in enumerate(detail_items, start=1)])
        controls.append(ft.Container(height=24))

        body = ft.Column(
            controls=controls,
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def artist_price_menu_by_id(menu_id):
        return get_artist_price_menu_by_id(menu_id)

    def portfolio_item_card(item, index):
        linked_menu = artist_price_menu_by_id(item.get("menu_id"))
        display_title = (linked_menu or {}).get("name") or item.get("title", "시술명")
        display_category = (linked_menu or {}).get("category") or item.get("category", "-")
        display_duration = (linked_menu or {}).get("duration") or item.get("duration", "")
        display_price = (linked_menu or {}).get("price") or item.get("price", "상담 후 안내")
        display_description = item.get("description") or (linked_menu or {}).get("description") or ""
        meta_parts = [display_category]
        if display_duration:
            meta_parts.append(display_duration)
        meta_parts.extend([item.get("style", "-"), display_price])

        def set_representative(e):
            for target in get_artist_portfolio_items():
                target["representative"] = target["id"] == item["id"]
            show_snack("대표 포트폴리오를 변경했어요.")
            show_artist_portfolio_page()

        def toggle_public(e):
            item["public"] = not item.get("public", True)
            show_artist_portfolio_page()

        def move_item(delta):
            def handler(e):
                items = get_artist_portfolio_items()
                next_index = index + delta
                if 0 <= next_index < len(items):
                    items[index], items[next_index] = items[next_index], items[index]
                    show_artist_portfolio_page()
            return handler

        def delete_item(e):
            app_state["artist_portfolio_items"] = [target for target in get_artist_portfolio_items() if target["id"] != item["id"]]
            show_snack("포트폴리오를 삭제했어요.")
            show_artist_portfolio_page()

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
                            ft.Container(width=72, height=72, border_radius=18, bgcolor="#000000"),
                            ft.Column(
                                controls=[
                                    ft.Text(display_title, size=15, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                                    ft.Text(" · ".join(meta_parts), size=11, color=SUBTEXT_COLOR),
                                    ft.Row(
                                        controls=[
                                            ft.Container(
                                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                                bgcolor=MAIN_COLOR_SOFT,
                                                border_radius=999,
                                                border=ft.border.all(1, BORDER_COLOR),
                                                content=ft.Text(
                                                    "가격 메뉴 연결됨" if linked_menu else "메뉴 연결 필요",
                                                    size=9,
                                                    color=MAIN_COLOR_DARK,
                                                    weight=ft.FontWeight.W_700,
                                                ),
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                    ft.Text(display_description, size=11, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            ft.TextButton("대표 설정" if not item.get("representative") else "대표 이미지", on_click=set_representative),
                            ft.TextButton("공개" if item.get("public", True) else "비공개", on_click=toggle_public),
                            ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_size=16, icon_color=MAIN_COLOR, on_click=move_item(-1)),
                            ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_size=16, icon_color=MAIN_COLOR, on_click=move_item(1)),
                            ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color="#B85C5C", on_click=delete_item),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=10,
            ),
        )

    def show_artist_portfolio_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_portfolio"
        app_state["selected_tab"] = 4

        def add_portfolio(e):
            app_state["current_page"] = "artist_portfolio_add"
            show_artist_portfolio_add_page()

        items = get_artist_portfolio_items()
        controls = [
            page_header("포트폴리오 관리", on_back=safe_go_back),
            ft.Text("가격 메뉴를 먼저 만들고, 포트폴리오에서 해당 메뉴를 연결해 노출해요.", size=12, color=SUBTEXT_COLOR, width=content_width()),
            soft_button("포트폴리오 추가", MAIN_COLOR, "#FFFFFF", add_portfolio, width=content_width()),
        ]
        controls.extend([portfolio_item_card(item, index) for index, item in enumerate(items)])
        controls.append(ft.Container(height=24))

        body = ft.Column(controls=controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        make_shell(body, app_state["selected_tab"])

    def show_artist_portfolio_add_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_portfolio_add"
        app_state["selected_tab"] = 4

        selected_style = ["감성"]
        selected_photo = [False]
        menu_items = get_artist_price_menus()
        selectable_menu_items = get_artist_price_menus(available_only=True) or menu_items
        selected_menu_id = [selectable_menu_items[0].get("id") if selectable_menu_items else None]
        menu_option_controls = []
        style_chips = []

        def portfolio_field(label, hint, multiline=False):
            return ft.Column(
                controls=[
                    ft.Text(label, size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                    ft.TextField(
                        width=content_width(),
                        hint_text=hint,
                        multiline=multiline,
                        min_lines=3 if multiline else 1,
                        max_lines=5 if multiline else 1,
                        border_color=BORDER_COLOR,
                        focused_border_color=MAIN_COLOR,
                        cursor_color=MAIN_COLOR,
                        bgcolor=CARD_COLOR,
                        border_radius=18,
                        content_padding=ft.padding.symmetric(horizontal=16, vertical=13),
                        text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
                        hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
                    ),
                ],
                spacing=8,
            )

        description_group = portfolio_field("설명 문구", "스타일 특징, 추천 얼굴형, 유지 팁을 짧게 적어주세요.", multiline=True)
        description_field = description_group.controls[1]

        public_switch = ft.Switch(value=True, active_color=MAIN_COLOR)
        representative_switch = ft.Switch(value=False, active_color=MAIN_COLOR)
        photo_status = ft.Text("사진을 선택하면 포트폴리오 썸네일로 사용돼요.", size=11, color=SUBTEXT_COLOR)
        photo_preview = ft.Container(
            width=92,
            height=92,
            border_radius=24,
            bgcolor="#000000",
            border=ft.border.all(1, BORDER_COLOR),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(app_icon("ADD_A_PHOTO_OUTLINED", "PHOTO_CAMERA"), size=24, color="#FFFFFF"),
        )

        def choose_photo(e):
            selected_photo[0] = True
            photo_status.value = "사진이 선택된 상태예요. 실제 업로드 API는 이후 연결하면 됩니다."
            photo_preview.border = ft.border.all(2, MAIN_COLOR)
            photo_status.update()
            photo_preview.update()

        def refresh_tag_chips(chips, selected_value):
            for chip, value in chips:
                active = selected_value[0] == value
                chip.bgcolor = MAIN_COLOR if active else CHIP_BG
                chip.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
                chip.content.color = "#FFFFFF" if active else TEXT_COLOR
                chip.content.weight = ft.FontWeight.W_800 if active else ft.FontWeight.W_600
                try:
                    chip.update()
                except Exception:
                    pass

        def choose_tag(chips, selected_value, value):
            def handler(e):
                selected_value[0] = value
                refresh_tag_chips(chips, selected_value)
            return handler

        def tag_chip(label, chips, selected_value):
            active = selected_value[0] == label
            chip = ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=9),
                border_radius=999,
                bgcolor=MAIN_COLOR if active else CHIP_BG,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                ink=True,
                on_click=choose_tag(chips, selected_value, label),
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_800 if active else ft.FontWeight.W_600,
                ),
            )
            chips.append((chip, label))
            return chip

        def tag_section(title, labels, chips, selected_value):
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                        ft.Row(
                            controls=[tag_chip(label, chips, selected_value) for label in labels],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=10,
                ),
            )

        def refresh_menu_options():
            for option in menu_option_controls:
                active = selected_menu_id[0] == option["id"]
                option["box"].bgcolor = MAIN_COLOR_SOFT if active else "#FFFFFF"
                option["box"].border = ft.border.all(1.4 if active else 1, MAIN_COLOR if active else BORDER_COLOR)
                option["title"].color = MAIN_COLOR_DARK if active else TEXT_COLOR
                option["title"].weight = ft.FontWeight.W_800 if active else ft.FontWeight.W_700
                option["check"].visible = active
                try:
                    option["box"].update()
                except Exception:
                    pass

        def choose_menu(menu_id):
            def handler(e):
                selected_menu_id[0] = menu_id
                refresh_menu_options()
            return handler

        def menu_option(item):
            active = selected_menu_id[0] == item.get("id")
            title_text = ft.Text(
                item.get("name", "시술명"),
                size=13,
                color=MAIN_COLOR_DARK if active else TEXT_COLOR,
                weight=ft.FontWeight.W_800 if active else ft.FontWeight.W_700,
            )
            check_icon = ft.Icon(
                app_icon("CHECK_CIRCLE", "CHECK_CIRCLE"),
                size=18,
                color=MAIN_COLOR,
                visible=active,
            )
            box = ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                bgcolor=MAIN_COLOR_SOFT if active else "#FFFFFF",
                border_radius=18,
                border=ft.border.all(1.4 if active else 1, MAIN_COLOR if active else BORDER_COLOR),
                ink=True,
                on_click=choose_menu(item.get("id")),
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                title_text,
                                ft.Text(
                                    f'{item.get("category", "-")} · {item.get("duration", "-")} · {item.get("price", "-")}',
                                    size=10,
                                    color=SUBTEXT_COLOR,
                                ),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        check_icon,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            menu_option_controls.append({"id": item.get("id"), "box": box, "title": title_text, "check": check_icon})
            return box

        def price_menu_selection_section():
            if not selectable_menu_items:
                return ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("연결할 가격 메뉴가 없어요", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                            ft.Text("포트폴리오는 가격 메뉴를 먼저 만든 뒤 연결해서 등록해요.", size=11, color=SUBTEXT_COLOR),
                            soft_button(
                                "가격 메뉴 만들기",
                                MAIN_COLOR,
                                "#FFFFFF",
                                lambda e: show_artist_price_menu_page(),
                                width=content_width() - 44,
                            ),
                        ],
                        spacing=10,
                    ),
                )

            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text("연결할 가격 메뉴", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                        ft.Text("먼저 등록한 시술 메뉴를 선택하면 시술명, 카테고리, 가격이 포트폴리오와 연결돼요.", size=10, color=SUBTEXT_COLOR),
                        *[menu_option(item) for item in selectable_menu_items],
                    ],
                    spacing=8,
                ),
            )

        def save_portfolio(e):
            linked_menu = artist_price_menu_by_id(selected_menu_id[0])
            if not linked_menu:
                show_snack("가격 메뉴를 먼저 선택해주세요.", bgcolor="#B85C5C")
                return

            items = get_artist_portfolio_items()
            if representative_switch.value:
                for target in items:
                    target["representative"] = False

            items.insert(0, {
                "id": f"portfolio_{len(items) + 1}",
                "menu_id": linked_menu.get("id"),
                "title": linked_menu.get("name", "시술명"),
                "category": linked_menu.get("category", "-"),
                "style": selected_style[0],
                "duration": linked_menu.get("duration", ""),
                "price": linked_menu.get("price", "상담 후 안내"),
                "description": (description_field.value or "").strip() or linked_menu.get("description") or "사진과 설명을 추가해 대표 스타일을 완성해보세요.",
                "public": bool(public_switch.value),
                "representative": bool(representative_switch.value),
                "has_photo": bool(selected_photo[0]),
            })
            record_artist_notification(
                "completion",
                "포트폴리오가 등록되었어요",
                f"{linked_menu.get('name', '시술명')} · 공개 상태를 확인하세요.",
                "artist_portfolio",
            )
            open_completion_feedback(
                "포트폴리오가 등록되었어요",
                "가격 메뉴와 포트폴리오 목록에 반영했어요.",
                "포트폴리오 관리로",
                "artist_portfolio",
                selected_tab=4,
                icon_name="IMAGE",
            )

        controls = [
            page_header("포트폴리오 추가", on_back=safe_go_back),
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_XL,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Row(
                    controls=[
                        photo_preview,
                        ft.Column(
                            controls=[
                                ft.Text("대표 사진", size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                photo_status,
                                soft_button("사진 선택", "#FFFFFF", MAIN_COLOR_DARK, choose_photo, border=ft.border.all(1, BORDER_COLOR), width=132),
                            ],
                            spacing=8,
                            expand=True,
                        ),
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            price_menu_selection_section(),
            tag_section("스타일 태그", ["감성", "트렌디", "내추럴", "고급스러운", "세련", "러블리"], style_chips, selected_style),
            description_group,
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("공개 상태", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700, expand=True),
                                public_switch,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("대표 이미지로 설정", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700, expand=True),
                                representative_switch,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=8,
                ),
            ),
            soft_button("저장하기", MAIN_COLOR, "#FFFFFF", save_portfolio, width=content_width()),
            soft_button("취소", "#FFFFFF", MAIN_COLOR_DARK, lambda e: show_artist_portfolio_page(), border=ft.border.all(1, BORDER_COLOR), width=content_width()),
            ft.Container(height=24),
        ]

        body = ft.Column(controls=controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        make_shell(body, app_state["selected_tab"])

    def show_artist_profile_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_profile"
        app_state["selected_tab"] = 4
        profile = get_artist_profile()

        def locked_profile_card(label, value):
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(label, size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                                ft.Text(value or "-", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            ],
                            spacing=6,
                            expand=True,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            bgcolor=MAIN_COLOR_SOFT,
                            border_radius=999,
                            border=ft.border.all(1, BORDER_COLOR),
                            content=ft.Text("컨펌 필요", size=9, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def profile_action_card(icon_name, title, subtitle, on_click):
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                ink=True,
                on_click=on_click,
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=16,
                            bgcolor=CHIP_BG,
                            border=ft.border.all(1, BORDER_COLOR),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon(icon_name), size=20, color=MAIN_COLOR),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(title, size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=MAIN_COLOR_DARK),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def profile_field(label, value, hint="", multiline=False):
            field = ft.TextField(
                width=content_width(),
                value=value,
                hint_text=hint,
                multiline=multiline,
                min_lines=3 if multiline else 1,
                max_lines=5 if multiline else 1,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                cursor_color=MAIN_COLOR,
                bgcolor="#FFFFFF",
                border_radius=22,
                content_padding=ft.padding.symmetric(horizontal=18, vertical=13),
                text_style=ft.TextStyle(size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
            )
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text(label, size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                        field,
                    ],
                    spacing=8,
                ),
            ), field

        career_card, career_field = profile_field("경력/소개 문구", profile.get("career", ""), "경력과 스타일 강점을 적어주세요.", multiline=True)
        instagram_card, instagram_field = profile_field("인스타그램/포트폴리오 링크", profile.get("instagram", ""), "예: @findy_artist")
        hours_card, hours_field = profile_field("영업시간", profile.get("hours", ""), "예: 화-토 11:00 - 20:00")

        consultation = ft.Switch(
            value=app_state.get("artist_consulting_enabled", True),
            active_color=MAIN_COLOR,
            on_change=lambda e: app_state.__setitem__("artist_consulting_enabled", bool(e.control.value)),
        )

        def save_profile(e):
            profile["career"] = (career_field.value or "").strip() or "경력과 소개 문구를 입력해보세요."
            profile["instagram"] = (instagram_field.value or "").strip() or "@findy_artist"
            profile["hours"] = (hours_field.value or "").strip() or "상담 후 안내"
            app_state["artist_consulting_enabled"] = bool(consultation.value)
            show_snack("소개, 링크, 영업시간을 저장했어요.")

        controls = [
            page_header("프로필 관리", on_back=safe_go_back),
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor=CARD_COLOR,
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text("주요 정보는 회사 컨펌 후 반영돼요.", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Text("아티스트 이름, 분야, 지역, 샵 이름은 명함/인스타/네이버 플레이스 자료 확인 뒤 수정됩니다.", size=11, color=SUBTEXT_COLOR),
                    ],
                    spacing=6,
                ),
            ),
            locked_profile_card("아티스트 이름", profile.get("name", "OO 아티스트")),
            locked_profile_card("분야", profile.get("field", "헤어 디자이너")),
            locked_profile_card("지역", profile.get("region", "강남")),
            locked_profile_card("샵이름", profile.get("shop", "OO 샵")),
            career_card,
            instagram_card,
            hours_card,
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Row(
                    controls=[
                        ft.Text("상담 가능 여부", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_600, expand=True),
                        consultation,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            profile_action_card("SCHEDULE", "예약시간 관리", "고객에게 열어둘 예약 가능 시간을 설정해요.", lambda e: show_artist_time_manage_page()),
            soft_button("저장하기", MAIN_COLOR, "#FFFFFF", save_profile, width=content_width()),
            ft.Container(height=24),
        ]
        body = ft.Column(controls=controls, spacing=SPACE_SM, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        make_shell(body, app_state["selected_tab"])

    def show_artist_reservation_manage_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_reservations"
        app_state["selected_tab"] = 4
        today = date.today()
        selected_date = app_state.get("artist_reservation_date", today.isoformat())
        selected_filter = app_state.get("artist_reservation_filter", "전체")
        reservation_actions = app_state.setdefault("artist_reservation_actions", {})
        reservation_memos = app_state.setdefault("artist_reservation_memos", {})
        active_request_editor = app_state.get("artist_reservation_request_editor") or {}
        active_memo_editor = app_state.get("artist_reservation_memo_editor") or {}
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]

        def add_months(base_date, offset):
            month_index = base_date.month - 1 + offset
            year = base_date.year + month_index // 12
            month = month_index % 12 + 1
            return date(year, month, 1)

        def day_label(target_date):
            if target_date == today:
                return "오늘"
            if target_date == today + timedelta(days=1):
                return "내일"
            return weekdays[target_date.weekday()]

        month_offset = safe_int(app_state.get("artist_reservation_month_offset", 0), default=0, minimum=0)
        app_state["artist_reservation_month_offset"] = month_offset
        month_anchor = add_months(today.replace(day=1), month_offset)
        selected_date_obj = safe_date_fromiso(selected_date, today)
        if selected_date_obj.year != month_anchor.year or selected_date_obj.month != month_anchor.month:
            selected_date_obj = today if today.year == month_anchor.year and today.month == month_anchor.month else month_anchor
            selected_date = selected_date_obj.isoformat()
            app_state["artist_reservation_date"] = selected_date

        reservation_items = [
            {
                "date": today.isoformat(),
                "time": "11:00",
                "customer": "김수아",
                "service": "레이어드컷 상담",
                "memo": "길이 유지, 얼굴형 보정 상담",
                "status": "예정",
                "request": "",
            },
            {
                "date": today.isoformat(),
                "time": "16:00",
                "customer": "한지민",
                "service": "빌드펌",
                "memo": "전후 사진 동의 확인 필요",
                "status": "예정",
                "request": "변경 요청 발송",
            },
            {
                "date": (today + timedelta(days=1)).isoformat(),
                "time": "13:00",
                "customer": "윤서하",
                "service": "애쉬그레이 컬러",
                "memo": "탈색 이력 확인",
                "status": "예정",
                "request": "",
            },
            {
                "date": (today + timedelta(days=2)).isoformat(),
                "time": "15:30",
                "customer": "박지연",
                "service": "빌드펌",
                "memo": "리뷰 요청 가능",
                "status": "완료",
                "request": "",
            },
            {
                "date": (today + timedelta(days=3)).isoformat(),
                "time": "10:30",
                "customer": "최서윤",
                "service": "포토 촬영",
                "memo": "고객 취소",
                "status": "취소/노쇼",
                "request": "취소 완료",
            },
            {
                "date": (today + timedelta(days=8)).isoformat(),
                "time": "14:00",
                "customer": "이민지",
                "service": "내추럴 레이어드",
                "memo": "첫 방문 고객",
                "status": "예정",
                "request": "",
            },
            {
                "date": (today + timedelta(days=13)).isoformat(),
                "time": "18:00",
                "customer": "정다은",
                "service": "톤다운 컬러",
                "memo": "퇴근 후 방문",
                "status": "예정",
                "request": "취소 요청 발송",
            },
            {
                "date": (today + timedelta(days=19)).isoformat(),
                "time": "12:00",
                "customer": "오하린",
                "service": "앞머리 컷",
                "memo": "짧은 시술",
                "status": "완료",
                "request": "",
            },
        ]

        status_meta = {
            "예정": ("예약 체결", MAIN_COLOR, "변경 요청"),
            "완료": ("완료된 시술", "#6C7A56", "리뷰 요청"),
            "취소/노쇼": ("취소/노쇼", "#9C6A5F", "기록"),
        }
        filters = ["전체", "예정", "완료", "취소/노쇼", "요청관리"]
        calendar_cell_width = max(34, int((content_width() - (SPACE_LG * 2) - (6 * 6)) / 7))
        calendar_day_controls = {}
        calendar_day_texts = {}
        calendar_count_texts = {}
        calendar_dots = {}
        calendar_dates = {}
        filter_chip_controls = {}
        filter_text_controls = {}

        def reservation_key(item):
            return f'{item["date"]}_{item["time"]}_{item["customer"]}_{item["service"]}'

        def reservation_action_text(item):
            return reservation_actions.get(reservation_key(item), item.get("request", ""))

        def reservation_memo_text(item):
            item_key = reservation_key(item)
            return reservation_memos[item_key] if item_key in reservation_memos else item.get("memo", "")

        def record_customer_request(item, request_type, message):
            app_state.setdefault("artist_customer_requests", []).insert(0, {
                "type": request_type,
                "customer": item["customer"],
                "service": item["service"],
                "date": item["date"],
                "time": item["time"],
                "message": message,
            })

        def current_selected_date():
            return app_state.get("artist_reservation_date", selected_date)

        def current_selected_filter():
            return app_state.get("artist_reservation_filter", selected_filter)

        def current_selected_date_obj():
            return safe_date_fromiso(current_selected_date(), today)

        def filtered_items():
            active_date = current_selected_date()
            active_filter = current_selected_filter()
            items = [item for item in reservation_items if item["date"] == active_date]
            if active_filter in status_meta:
                items = [item for item in items if item["status"] == active_filter]
            elif active_filter == "요청관리":
                items = [item for item in items if reservation_action_text(item)]
            return sorted(items, key=lambda item: item["time"])

        def selected_schedule_label():
            target_date = current_selected_date_obj()
            return f"{target_date.month}월 {target_date.day}일 {day_label(target_date)} 일정"

        def summary_card(label, value, note):
            return ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=10, vertical=12),
                bgcolor=CARD_COLOR,
                border_radius=18,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text(label, size=10, color=SUBTEXT_COLOR),
                        ft.Text(value, size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Text(note, size=9, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                    ],
                    spacing=3,
                ),
            )

        def change_month(delta):
            def handle(e):
                next_offset = max(0, safe_int(app_state.get("artist_reservation_month_offset", 0), default=0) + delta)
                next_month = add_months(today.replace(day=1), next_offset)
                app_state["artist_reservation_month_offset"] = next_offset
                app_state["artist_reservation_date"] = (today if today.year == next_month.year and today.month == next_month.month else next_month).isoformat()
                show_artist_reservation_manage_page()

            return handle

        def apply_calendar_day_style(iso_value):
            cell = calendar_day_controls.get(iso_value)
            target_date = calendar_dates.get(iso_value)
            if not cell or target_date is None:
                return
            active = current_selected_date() == iso_value
            is_today = target_date == today
            day_items = [item for item in reservation_items if item["date"] == iso_value]
            has_request = any(reservation_action_text(item) for item in day_items)
            cell.bgcolor = MAIN_COLOR if active else "#FFFFFF"
            cell.border = ft.border.all(1, MAIN_COLOR if active else (MAIN_COLOR_SOFT if is_today else "transparent"))
            day_text = calendar_day_texts.get(iso_value)
            if day_text:
                day_text.color = "#FFFFFF" if active else SUBTEXT_COLOR
                day_text.weight = ft.FontWeight.W_800 if active or is_today else ft.FontWeight.W_600
            count_text = calendar_count_texts.get(iso_value)
            if count_text:
                count_text.color = "#FFFFFF" if active else MAIN_COLOR_DARK
            dot = calendar_dots.get(iso_value)
            if dot:
                dot.bgcolor = "#FFFFFF" if active and has_request else (MAIN_COLOR if has_request else "transparent")
            try:
                cell.update()
            except Exception:
                pass

        def refresh_filter_chip(label):
            chip = filter_chip_controls.get(label)
            text = filter_text_controls.get(label)
            if not chip or not text:
                return
            active = current_selected_filter() == label
            chip.bgcolor = MAIN_COLOR if active else CHIP_BG
            chip.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
            text.color = "#FFFFFF" if active else TEXT_COLOR
            text.weight = ft.FontWeight.W_700 if active else ft.FontWeight.W_600
            try:
                chip.update()
            except Exception:
                pass

        def calendar_day_cell(target_date):
            if target_date is None:
                return ft.Container(width=calendar_cell_width, height=56)
            iso_value = target_date.isoformat()
            active = current_selected_date() == iso_value
            is_today = target_date == today

            def handle(e):
                previous_date = current_selected_date()
                app_state["artist_reservation_date"] = iso_value
                apply_calendar_day_style(previous_date)
                apply_calendar_day_style(iso_value)
                refresh_schedule_section()

            day_items = [item for item in reservation_items if item["date"] == iso_value]
            has_request = any(reservation_action_text(item) for item in day_items)
            day_text = ft.Text(
                str(target_date.day),
                size=14,
                color="#FFFFFF" if active else SUBTEXT_COLOR,
                weight=ft.FontWeight.W_800 if active or is_today else ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            )
            count_text = ft.Text(
                f"{len(day_items)}건" if day_items else "",
                size=8,
                color="#FFFFFF" if active else MAIN_COLOR_DARK,
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.CENTER,
            )
            dot = ft.Container(
                width=6,
                height=6,
                border_radius=999,
                bgcolor="#FFFFFF" if active and has_request else (MAIN_COLOR if has_request else "transparent"),
            )
            cell = ft.Container(
                width=calendar_cell_width,
                height=56,
                padding=ft.padding.symmetric(horizontal=4, vertical=6),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=15,
                border=ft.border.all(1, MAIN_COLOR if active else (MAIN_COLOR_SOFT if is_today else "transparent")),
                on_click=handle,
                ink=True,
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                content=ft.Column(
                    controls=[
                        day_text,
                        count_text,
                        dot,
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            calendar_day_controls[iso_value] = cell
            calendar_day_texts[iso_value] = day_text
            calendar_count_texts[iso_value] = count_text
            calendar_dots[iso_value] = dot
            calendar_dates[iso_value] = target_date
            return cell

        def month_calendar():
            first_weekday, day_count = calendar.monthrange(month_anchor.year, month_anchor.month)
            days = [None] * first_weekday + [date(month_anchor.year, month_anchor.month, day) for day in range(1, day_count + 1)]
            while len(days) % 7:
                days.append(None)

            rows = []
            for start in range(0, len(days), 7):
                rows.append(
                    ft.Row(
                        controls=[calendar_day_cell(day) for day in days[start:start + 7]],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            return ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(day, size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700, width=calendar_cell_width, text_align=ft.TextAlign.CENTER)
                            for day in weekdays
                        ],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    *rows,
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        def filter_chip(label):
            active = current_selected_filter() == label

            def handle(e):
                previous_filter = current_selected_filter()
                app_state["artist_reservation_filter"] = label
                refresh_filter_chip(previous_filter)
                refresh_filter_chip(label)
                refresh_schedule_section()

            label_text = ft.Text(
                label,
                size=11,
                color="#FFFFFF" if active else TEXT_COLOR,
                weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_600,
            )
            chip = ft.Container(
                padding=ft.padding.symmetric(horizontal=13, vertical=8),
                bgcolor=MAIN_COLOR if active else CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=handle,
                ink=True,
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                content=label_text,
            )
            filter_chip_controls[label] = chip
            filter_text_controls[label] = label_text
            return chip

        def reservation_card(item):
            label, color, action_text = status_meta[item["status"]]
            request_text = reservation_action_text(item)
            item_key = reservation_key(item)
            memo_text = reservation_memo_text(item)
            request_kind = {"value": None}
            request_text_value = ft.Text(
                request_text or "",
                size=10,
                color=MAIN_COLOR_DARK,
                weight=ft.FontWeight.W_700,
            )
            memo_display_text = ft.Text(memo_text or "메모 없음", size=11, color=SUBTEXT_COLOR)
            request_title = ft.Text("", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800)
            request_subtitle = ft.Text(f"{item['customer']}님에게 문자처럼 전달돼요.", size=10, color=SUBTEXT_COLOR)
            request_message_field = ft.TextField(
                hint_text="",
                value="",
                multiline=True,
                min_lines=3,
                max_lines=5,
                border_radius=16,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
                hint_style=ft.TextStyle(size=13, color="#B8AA9E"),
            )
            memo_field = ft.TextField(
                hint_text="예약 관련 메모를 적어주세요.",
                value=memo_text,
                multiline=True,
                min_lines=4,
                max_lines=6,
                border_radius=16,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
                hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
            )

            def send_action(message):
                def handle(e):
                    reservation_actions[item_key] = message
                    record_customer_request(item, message, message)
                    request_text_value.value = message
                    request_status_box.visible = True
                    request_status_box.update()
                    show_snack(f"{item['customer']}님에게 {message} 알림을 보냈어요.")

                return handle

            def open_request_editor(kind):
                def handle(e):
                    request_kind["value"] = kind
                    request_title.value = "변경 가능 시간 메시지" if kind == "change" else "취소 요청 메시지"
                    request_subtitle.value = f"{item['customer']}님에게 문자처럼 전달돼요."
                    request_message_field.value = ""
                    request_message_field.hint_text = (
                        "예) 아티스트 사정으로 인해 X월 X일 X시로 예약 변경 가능하실까요? 감사합니다 :)"
                        if kind == "change"
                        else "예) 아티스트 사정으로 인해 예약 취소 요청드립니다. 확인 부탁드려요. 감사합니다 :)"
                    )
                    memo_editor_box.visible = False
                    request_editor_box.visible = True
                    memo_editor_box.update()
                    request_editor_box.update()

                return handle

            def submit_request(event):
                message_body = (request_message_field.value or "").strip()
                if not message_body:
                    show_snack("고객에게 보낼 메시지를 입력해주세요.")
                    return
                message_label = "변경 요청 메시지" if request_kind["value"] == "change" else "취소 요청 메시지"
                snack_text = "변경 요청" if request_kind["value"] == "change" else "취소 요청"
                reservation_actions[item_key] = f"{message_label}\n{message_body}"
                record_customer_request(item, message_label, message_body)
                request_text_value.value = f"{message_label}\n{message_body}"
                request_status_box.visible = True
                request_editor_box.visible = False
                request_status_box.update()
                request_editor_box.update()
                show_snack(f"{item['customer']}님에게 {snack_text} 알림을 보냈어요.")

            def cancel_request_editor(event):
                request_editor_box.visible = False
                request_editor_box.update()

            request_editor_box = ft.Container(
                visible=False,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                padding=ft.padding.symmetric(horizontal=12, vertical=12),
                bgcolor=CARD_COLOR,
                border_radius=18,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=34,
                                height=34,
                                border_radius=14,
                                bgcolor=MAIN_COLOR_SOFT,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(
                                    app_icon("CHAT_BUBBLE_OUTLINE", "CHAT_BUBBLE"),
                                    size=17,
                                    color=MAIN_COLOR,
                                ),
                            ),
                            ft.Column(
                                controls=[
                                    request_title,
                                    request_subtitle,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=9,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    request_message_field,
                    ft.Row(
                        controls=[
                            soft_button("메시지 보내기", MAIN_COLOR, "white", submit_request, width=128),
                            soft_button("닫기", "#FFFFFF", MAIN_COLOR_DARK, cancel_request_editor, width=86),
                        ],
                        spacing=8,
                    ),
                    ],
                    spacing=9,
                ),
            )

            def open_memo(e):
                memo_field.value = reservation_memos.get(item_key, memo_display_text.value if memo_display_text.value != "메모 없음" else "")
                request_editor_box.visible = False
                memo_editor_box.visible = True
                request_editor_box.update()
                memo_editor_box.update()

            def save_memo(event):
                new_memo = (memo_field.value or "").strip()
                reservation_memos[item_key] = new_memo
                memo_display_text.value = new_memo or "메모 없음"
                memo_editor_box.visible = False
                memo_display_text.update()
                memo_editor_box.update()
                show_snack("예약 메모를 저장했어요.")

            def cancel_memo(event):
                memo_editor_box.visible = False
                memo_editor_box.update()

            memo_editor_box = ft.Container(
                visible=False,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                padding=ft.padding.symmetric(horizontal=12, vertical=12),
                bgcolor=CARD_COLOR,
                border_radius=18,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=34,
                                        height=34,
                                        border_radius=14,
                                        bgcolor=MAIN_COLOR_SOFT,
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(app_icon("EDIT_NOTE", "EDIT"), size=17, color=MAIN_COLOR),
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text("예약 메모", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                            ft.Text(f"{item['customer']} · {item['service']} · {item['time']}", size=10, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                ],
                                spacing=9,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            memo_field,
                            ft.Row(
                                controls=[
                                    soft_button("저장", MAIN_COLOR, "white", save_memo, width=86),
                                    soft_button("닫기", "#FFFFFF", MAIN_COLOR_DARK, cancel_memo, width=86),
                                ],
                                spacing=8,
                            ),
                    ],
                    spacing=12,
                ),
            )

            primary_action = send_action("리뷰 요청 발송") if item["status"] == "완료" else open_request_editor("change")
            cancel_action = open_request_editor("cancel")
            request_status_box = ft.Container(
                visible=bool(request_text),
                padding=ft.padding.symmetric(horizontal=11, vertical=8),
                bgcolor=MAIN_COLOR_SOFT,
                border_radius=14,
                content=request_text_value,
            )
            action_controls = [
                soft_button(action_text, MAIN_COLOR, "white", primary_action, width=100),
                soft_button("취소 요청", "#FFFFFF", MAIN_COLOR_DARK, cancel_action, width=92),
                soft_button("메모", "#FFFFFF", MAIN_COLOR_DARK, open_memo, width=68),
            ]
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=16, vertical=16),
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Container(
                                            width=52,
                                            height=52,
                                            border_radius=18,
                                            bgcolor=MAIN_COLOR_SOFT,
                                            alignment=ft.Alignment(0, 0),
                                            content=ft.Text(item["time"], size=12, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                        ),
                                        ft.Container(width=2, height=46, bgcolor=BORDER_COLOR, border_radius=999),
                                    ],
                                    spacing=8,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text(item["customer"], size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800, expand=True),
                                                ft.Container(
                                                    padding=ft.padding.symmetric(horizontal=9, vertical=5),
                                                    bgcolor=ft.Colors.with_opacity(0.14, color),
                                                    border_radius=999,
                                                    content=ft.Text(label, size=9, color=color, weight=ft.FontWeight.W_700),
                                                ),
                                            ],
                                            spacing=8,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        ft.Text(item["service"], size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                                        ft.Row(
                                            controls=[
                                                ft.Icon(app_icon("NOTES", "SUBJECT"), size=14, color=SUBTEXT_COLOR),
                                                ft.Container(expand=True, content=memo_display_text),
                                            ],
                                            spacing=5,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        request_status_box,
                                        ft.Row(
                                            controls=action_controls,
                                            spacing=8,
                                            scroll=ft.ScrollMode.HIDDEN,
                                        ),
                                    ],
                                    spacing=8,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        request_editor_box,
                        memo_editor_box,
                    ],
                    spacing=10,
                ),
            )

        def time_manage_card():
            available_slots = app_state.get("artist_available_slots", ["11:00", "12:30", "15:00", "17:30", "19:00"])
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
                                        ft.Text("예약 시간 관리", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text("선택한 날짜의 예약 가능 시간을 빠르게 확인해요.", size=11, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                    bgcolor=MAIN_COLOR_SOFT,
                                    border_radius=999,
                                    content=ft.Text(f"{len(available_slots)}개 가능", size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=11, vertical=8),
                                    bgcolor=CHIP_BG,
                                    border_radius=999,
                                    border=ft.border.all(1, BORDER_COLOR),
                                    content=ft.Text(slot, size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                                )
                                for slot in available_slots
                            ],
                            spacing=7,
                            scroll=ft.ScrollMode.HIDDEN,
                        ),
                        soft_button("가능 시간 수정", MAIN_COLOR, "white", lambda e: show_artist_time_manage_page(), width=content_width() - 44),
                    ],
                    spacing=14,
                ),
            )

        def empty_schedule_card():
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    controls=[
                        ft.Icon(app_icon("EVENT_AVAILABLE", "CALENDAR_MONTH"), size=30, color=MAIN_COLOR),
                        ft.Text("선택한 조건의 예약이 없어요.", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                        ft.Text("다른 날짜나 상태를 선택해보세요.", size=11, color=SUBTEXT_COLOR),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def build_schedule_controls():
            items = filtered_items()
            if items:
                return [reservation_card(item) for item in items]
            return [empty_schedule_card()]

        schedule_title_text = ft.Text(
            selected_schedule_label(),
            size=15,
            color=TEXT_COLOR,
            weight=ft.FontWeight.W_800,
        )
        schedule_list = ft.Column(
            controls=build_schedule_controls(),
            spacing=SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            animate_opacity=ft.Animation(130, ft.AnimationCurve.EASE_OUT),
        )

        def refresh_schedule_section():
            schedule_title_text.value = selected_schedule_label()
            schedule_list.opacity = 0.72
            schedule_list.controls = build_schedule_controls()
            try:
                schedule_title_text.update()
                schedule_list.update()
            except Exception:
                pass

            async def settle():
                await asyncio.sleep(0.03)
                try:
                    schedule_list.opacity = 1
                    schedule_list.update()
                except Exception:
                    pass

            page.run_task(settle)

        today_items = [item for item in reservation_items if item["date"] == today.isoformat()]
        month_items = [
            item
            for item in reservation_items
            if date.fromisoformat(item["date"]).year == month_anchor.year
            and date.fromisoformat(item["date"]).month == month_anchor.month
        ]
        request_total = len([item for item in reservation_items if reservation_action_text(item)])
        upcoming_total = len([item for item in reservation_items if item["status"] == "예정"])

        controls = [
            page_header("예약 관리", on_back=safe_go_back),
            ft.Row(
                controls=[
                    summary_card("오늘 예약", f"{len(today_items)}건", "오늘 일정"),
                    ft.Container(width=8),
                    summary_card("변경/취소", f"{request_total}건", "요청 알림"),
                    ft.Container(width=8),
                    summary_card("이번 달", f"{len(month_items)}건", "체결 예약"),
                ],
                spacing=0,
                width=content_width(),
            ),
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
                                ft.Column(
                                    controls=[
                                        ft.Text("월간 예약 달력", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text("고객 예약은 바로 체결되고, 변경/취소는 알림 요청으로 관리해요.", size=11, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Icon(app_icon("CALENDAR_MONTH", "EVENT_NOTE"), size=22, color=MAIN_COLOR),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(icon=app_icon("CHEVRON_LEFT", "ARROW_BACK_IOS_NEW"), icon_size=18, icon_color=TEXT_COLOR, on_click=change_month(-1)),
                                ft.Text(f"{month_anchor.year}년 {month_anchor.month}월", size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_800, expand=True, text_align=ft.TextAlign.CENTER),
                                ft.IconButton(icon=app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), icon_size=18, icon_color=TEXT_COLOR, on_click=change_month(1)),
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        month_calendar(),
                    ],
                    spacing=14,
                ),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            ft.Row(
                controls=[filter_chip(label) for label in filters],
                spacing=8,
                scroll=ft.ScrollMode.HIDDEN,
            ),
            ft.Container(
                width=content_width(),
                content=schedule_title_text,
            ),
            schedule_list,
        ]
        controls.append(ft.Container(height=24))
        body = ft.Column(controls=controls, spacing=SPACE_SM, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        make_shell(body, app_state["selected_tab"])

    def show_artist_time_manage_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_time_manage"
        app_state["selected_tab"] = 4

        available_order = ["10:00", "10:30", "11:00", "12:30", "14:00", "15:00", "16:30", "17:30", "19:00"]
        active_slots = set(app_state.get("artist_available_slots", ["11:00", "12:30", "15:00", "17:30", "19:00"]))
        slot_controls = {}
        count_text = ft.Text("", size=12, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700)

        def save_active_slots():
            app_state["artist_available_slots"] = [slot for slot in available_order if slot in active_slots]
            count_text.value = f"{len(active_slots)}개 시간 열림"

        def refresh_slot(slot):
            control = slot_controls.get(slot)
            if not control:
                return
            active = slot in active_slots
            control.bgcolor = MAIN_COLOR if active else "#FFFFFF"
            control.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
            control.content.value = slot
            control.content.color = "#FFFFFF" if active else TEXT_COLOR
            control.content.weight = ft.FontWeight.W_800 if active else ft.FontWeight.W_600
            try:
                control.update()
            except Exception:
                pass

        def toggle_slot(slot):
            def handle(e):
                if slot in active_slots:
                    active_slots.discard(slot)
                else:
                    active_slots.add(slot)
                save_active_slots()
                refresh_slot(slot)
                try:
                    count_text.update()
                except Exception:
                    pass

            return handle

        def slot_chip(slot):
            active = slot in active_slots
            chip = ft.Container(
                width=86,
                height=46,
                border_radius=999,
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=toggle_slot(slot),
                content=ft.Text(
                    slot,
                    size=13,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_800 if active else ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
            )
            slot_controls[slot] = chip
            return chip

        def select_all(e):
            active_slots.clear()
            active_slots.update(available_order)
            save_active_slots()
            for slot in available_order:
                refresh_slot(slot)
            count_text.update()

        def clear_all(e):
            active_slots.clear()
            save_active_slots()
            for slot in available_order:
                refresh_slot(slot)
            count_text.update()

        def save_and_back(e):
            save_active_slots()
            show_snack("예약 가능 시간을 저장했어요.")
            show_artist_profile_page()

        save_active_slots()
        body = ft.Column(
            controls=[
                page_header("예약시간 관리", on_back=safe_go_back),
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
                                    ft.Column(
                                        controls=[
                                            ft.Text("예약 가능 시간", size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                            ft.Text("고객에게 열어둘 시간을 선택해주세요.", size=12, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=11, vertical=7),
                                        bgcolor=MAIN_COLOR_SOFT,
                                        border_radius=999,
                                        content=count_text,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(height=1, bgcolor=BORDER_COLOR),
                            ft.Row(
                                controls=[slot_chip(slot) for slot in available_order],
                                spacing=9,
                                run_spacing=9,
                                wrap=True,
                            ),
                            ft.Row(
                                controls=[
                                    soft_button("전체 열기", "#FFFFFF", MAIN_COLOR_DARK, select_all, width=110),
                                    soft_button("전체 닫기", "#FFFFFF", MAIN_COLOR_DARK, clear_all, width=110),
                                ],
                                spacing=8,
                            ),
                            soft_button("저장하기", MAIN_COLOR, "white", save_and_back, width=content_width() - 44),
                        ],
                        spacing=16,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_artist_price_menu_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_price_menu"
        app_state["selected_tab"] = 4

        menu_items = get_artist_price_menus()
        selected_category = [get_artist_profile().get("category", "헤어")]
        category_chip_controls = []

        def menu_text_field(label, hint, *, multiline=False):
            field = ft.TextField(
                width=content_width(),
                hint_text=hint,
                multiline=multiline,
                min_lines=3 if multiline else 1,
                max_lines=4 if multiline else 1,
                border_radius=18,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                cursor_color=MAIN_COLOR,
                bgcolor="#FFFFFF",
                content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
                text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
                hint_style=ft.TextStyle(size=12, color=SUBTEXT_COLOR),
            )
            return ft.Column(
                controls=[
                    ft.Text(label, size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                    field,
                ],
                spacing=7,
            ), field

        def refresh_category_chips():
            for chip, label, text in category_chip_controls:
                active = selected_category[0] == label
                chip.bgcolor = MAIN_COLOR if active else "#FFFFFF"
                chip.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
                text.color = "#FFFFFF" if active else TEXT_COLOR
                text.weight = ft.FontWeight.W_800 if active else ft.FontWeight.W_600
                try:
                    chip.update()
                except Exception:
                    pass

        def choose_category(label):
            def handle(e):
                selected_category[0] = label
                refresh_category_chips()
            return handle

        def category_chip(label):
            active = selected_category[0] == label
            text = ft.Text(
                label,
                size=11,
                color="#FFFFFF" if active else TEXT_COLOR,
                weight=ft.FontWeight.W_800 if active else ft.FontWeight.W_600,
            )
            chip = ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                ink=True,
                on_click=choose_category(label),
                content=text,
            )
            category_chip_controls.append((chip, label, text))
            return chip

        name_group, name_field = menu_text_field("시술명", "예: 레이어드컷 상담")
        duration_group, duration_field = menu_text_field("소요 시간", "예: 60분")
        price_group, price_field = menu_text_field("가격", "예: 12만원대 / 상담 후 안내")
        desc_group, desc_field = menu_text_field("설명", "고객이 예약 전에 확인할 설명을 적어주세요.", multiline=True)
        available_switch = ft.Switch(value=True, active_color=MAIN_COLOR)

        def save_menu_item(e):
            name = (name_field.value or "").strip()
            if not name:
                show_snack("시술명을 입력해주세요.", bgcolor="#B85C5C")
                return
            menu_items.insert(0, {
                "id": f"menu_{len(menu_items) + 1}",
                "name": name,
                "category": selected_category[0],
                "duration": (duration_field.value or "").strip() or "상담 후 안내",
                "price": (price_field.value or "").strip() or "상담 후 안내",
                "description": (desc_field.value or "").strip() or "상세 설명을 입력해보세요.",
                "available": bool(available_switch.value),
            })
            show_snack("가격 메뉴를 추가했어요.")
            show_artist_price_menu_page()

        def menu_item_card(item):
            availability_text = ft.Text(
                "예약 가능" if item.get("available", True) else "예약 중지",
                size=10,
                color=MAIN_COLOR_DARK,
                weight=ft.FontWeight.W_700,
            )

            def toggle_available(e):
                item["available"] = not item.get("available", True)
                availability_text.value = "예약 가능" if item.get("available", True) else "예약 중지"
                availability_text.update()
                show_snack("예약 가능 여부를 변경했어요.")

            def delete_menu(e):
                app_state["artist_price_menu_items"] = [target for target in menu_items if target.get("id") != item.get("id")]
                show_snack("가격 메뉴를 삭제했어요.")
                show_artist_price_menu_page()

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
                                        ft.Text(item.get("name", "시술명"), size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text(f'{item.get("category", "-")} · {item.get("duration", "-")} · {item.get("price", "-")}', size=11, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                    bgcolor=MAIN_COLOR_SOFT,
                                    border_radius=999,
                                    border=ft.border.all(1, BORDER_COLOR),
                                    content=availability_text,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(item.get("description", ""), size=11, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row(
                            controls=[
                                soft_button("예약 상태 변경", "#FFFFFF", MAIN_COLOR_DARK, toggle_available, border=ft.border.all(1, BORDER_COLOR), width=128),
                                soft_button("삭제", "#FFFFFF", "#B85C5C", delete_menu, border=ft.border.all(1, BORDER_COLOR), width=74),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=10,
                ),
            )

        add_card = ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Text("새 시술 메뉴 추가", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                    ft.Row(
                        controls=[category_chip(label) for label in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]],
                        spacing=7,
                        run_spacing=7,
                        wrap=True,
                    ),
                    name_group,
                    ft.Row(
                        controls=[
                            ft.Container(expand=True, content=duration_group),
                            ft.Container(width=8),
                            ft.Container(expand=True, content=price_group),
                        ],
                        spacing=0,
                    ),
                    desc_group,
                    ft.Row(
                        controls=[
                            ft.Text("예약 가능 여부", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700, expand=True),
                            available_switch,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    soft_button("메뉴 추가", MAIN_COLOR, "#FFFFFF", save_menu_item, width=content_width() - 44),
                ],
                spacing=13,
            ),
        )

        controls = [
            page_header("가격 메뉴 관리", on_back=safe_go_back),
            ft.Container(
                width=content_width(),
                content=ft.Text("고객에게 노출될 시술명, 소요 시간, 가격, 예약 가능 여부를 정리해요.", size=12, color=SUBTEXT_COLOR),
            ),
            add_card,
            ft.Container(
                width=content_width(),
                content=ft.Text("등록된 메뉴", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
            ),
        ]
        controls.extend([menu_item_card(item) for item in menu_items])
        controls.append(ft.Container(height=24))

        body = ft.Column(controls=controls, spacing=SPACE_SM, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        make_shell(body, app_state["selected_tab"])

    def show_artist_review_manage_page():
        clear_transient_ui()
        app_state["current_page"] = "artist_reviews"
        app_state["selected_tab"] = 4
        profile = get_artist_profile()
        reviews = [item for item in REVIEW_ITEMS if review_item_category(item) == profile.get("category", "헤어")]
        controls = [
            page_header("리뷰 관리", on_back=safe_go_back),
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Row(
                    controls=[
                        artist_summary_stat("별점 평균", "4.8"),
                        ft.Container(width=8),
                        artist_summary_stat("받은 리뷰", len(reviews)),
                        ft.Container(width=8),
                        artist_summary_stat("사진 리뷰", 6),
                    ],
                ),
            ),
        ]
        for item in reviews[:4]:
            review_name = review_item_name(item)
            review_body = review_item_body(item)
            review_key = f"{review_name}_{review_item_category(item)}_{review_body[:18]}"
            review_replies = app_state.setdefault("artist_review_replies", {})
            review_hidden_requests = app_state.setdefault("artist_review_hidden_requests", set())
            reply_field = ft.TextField(
                hint_text="리뷰에 남길 답글을 입력해주세요.",
                value=review_replies.get(review_key, ""),
                multiline=True,
                min_lines=2,
                max_lines=4,
                border_radius=16,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                text_style=ft.TextStyle(size=12, color=TEXT_COLOR),
                hint_style=ft.TextStyle(size=12, color=SUBTEXT_COLOR),
            )
            reply_status = ft.Text(
                f"답글: {review_replies.get(review_key, '')}",
                size=11,
                color=MAIN_COLOR_DARK,
                weight=ft.FontWeight.W_700,
                visible=bool(review_replies.get(review_key)),
            )
            hide_status = ft.Text(
                "신고/숨김 요청을 접수했어요.",
                size=11,
                color="#9C6A5F",
                weight=ft.FontWeight.W_700,
                visible=review_key in review_hidden_requests,
            )
            reply_editor = ft.Container(
                visible=False,
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                padding=ft.padding.symmetric(horizontal=12, vertical=12),
                bgcolor=CARD_COLOR,
                border_radius=18,
                border=ft.border.all(1, BORDER_COLOR),
            )
            photo_review_box = ft.Container(
                visible=False,
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                content=ft.Row(
                    controls=[
                        black_image_box(76, 76),
                        black_image_box(76, 76),
                        black_image_box(76, 76),
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )

            def open_reply_editor(e, editor=reply_editor, photos=photo_review_box):
                photos.visible = False
                editor.visible = not editor.visible
                photos.update()
                editor.update()

            def save_reply(e, key=review_key, field=reply_field, status=reply_status, editor=reply_editor):
                value = (field.value or "").strip()
                if not value:
                    show_snack("답글 내용을 입력해주세요.", bgcolor="#B85C5C")
                    return
                review_replies[key] = value
                status.value = f"답글: {value}"
                status.visible = True
                editor.visible = False
                status.update()
                editor.update()
                show_snack("리뷰 답글을 저장했어요.")

            def toggle_photo_review(e, photos=photo_review_box, editor=reply_editor):
                editor.visible = False
                photos.visible = not photos.visible
                editor.update()
                photos.update()

            def request_hide(e, key=review_key, status=hide_status):
                review_hidden_requests.add(key)
                status.visible = True
                status.update()
                show_snack("신고/숨김 요청을 보냈어요.")

            reply_editor.content = ft.Column(
                controls=[
                    reply_field,
                    ft.Row(
                        controls=[
                            soft_button("답글 저장", MAIN_COLOR, "white", save_reply, width=100),
                            soft_button("닫기", "#FFFFFF", MAIN_COLOR_DARK, lambda e, editor=reply_editor: (setattr(editor, "visible", False), editor.update()), width=78),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=10,
            )
            controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(review_name, size=15, weight=ft.FontWeight.W_700, color=TEXT_COLOR, expand=True),
                                    ft.Text("★★★★★", size=13, color="#F2B84B"),
                                ],
                            ),
                            ft.Text(review_body, size=12, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            reply_status,
                            hide_status,
                            ft.Row(
                                controls=[
                                    ft.TextButton("답글 작성", on_click=open_reply_editor),
                                    ft.TextButton("사진 리뷰 보기", on_click=toggle_photo_review),
                                    ft.TextButton("신고/숨김 요청", on_click=request_hide),
                                ],
                            ),
                            photo_review_box,
                            reply_editor,
                        ],
                        spacing=8,
                    ),
                )
            )
        controls.append(ft.Container(height=24))
        body = ft.Column(controls=controls, spacing=SPACE_SM, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
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

        month_offset = safe_int(app_state.get("reservation_month_offset", 0), default=0, minimum=0)
        app_state["reservation_month_offset"] = month_offset
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
                "past": {"bg": CARD_COLOR, "border": BORDER_COLOR, "text": MUTED_TEXT_COLOR},
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
                                    ft.Row(controls=[ft.Container(width=10, height=10, border_radius=999, bgcolor=CARD_COLOR), ft.Text("지난 시간", size=10, color=SUBTEXT_COLOR)], spacing=6),
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

        def message_click(e):
            start_customer_chat_with_artist(artist, "detail")

        saved = is_saved(artist["id"])
        review_count = max(1, len([item for item in REVIEW_ITEMS if review_item_category(item) == artist.get("category")]))
        portfolio_media = [
            {"type": "photo", "title": f"{artist['style']} 대표컷", "tag": artist["category"]},
            {"type": "photo", "title": artist["reason"], "tag": artist["tags"][0] if artist.get("tags") else artist["category"]},
            {"type": "video", "title": f"{artist['category']} 시술 과정", "tag": "영상"},
            {"type": "photo", "title": artist["intro"], "tag": artist["tags"][1] if len(artist.get("tags", [])) > 1 else "포트폴리오"},
            {"type": "photo", "title": f"{artist['name']} 무드컷", "tag": "무드"},
            {"type": "video", "title": "비포 애프터", "tag": "영상"},
            {"type": "photo", "title": "디테일 컷", "tag": "디테일"},
            {"type": "photo", "title": "고객 후기 스타일", "tag": "리뷰"},
            {"type": "photo", "title": "추천 스타일", "tag": "추천"},
        ]

        def stat_block(label, value):
            return ft.Container(
                expand=True,
                padding=ft.padding.symmetric(vertical=12),
                border_radius=RADIUS_MD,
                border=ft.border.all(1, BORDER_COLOR),
                bgcolor="#FFFFFF",
                content=ft.Column(
                    controls=[
                        ft.Text(str(value), size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                        ft.Text(label, size=11, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=3,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        save_icon = ft.Icon(
            ft.Icons.BOOKMARK if saved else ft.Icons.BOOKMARK_BORDER,
            size=23,
            color=MAIN_COLOR if saved else SUBTEXT_COLOR,
        )
        save_button = ft.Container(
            width=54,
            height=48,
            border_radius=RADIUS_MD,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, MAIN_COLOR if saved else BORDER_COLOR),
            alignment=ft.Alignment(0, 0),
            ink=True,
            content=save_icon,
        )

        def save_click_local(e):
            toggle_saved(artist["id"])
            current = is_saved(artist["id"])
            save_icon.name = ft.Icons.BOOKMARK if current else ft.Icons.BOOKMARK_BORDER
            save_icon.color = MAIN_COLOR if current else SUBTEXT_COLOR
            save_button.border = ft.border.all(1, MAIN_COLOR if current else BORDER_COLOR)
            save_button.update()

        portfolio_filter = app_state.get("detail_portfolio_filter", "전체")
        if portfolio_filter not in {"전체", "사진", "영상"}:
            portfolio_filter = "전체"
            app_state["detail_portfolio_filter"] = portfolio_filter

        filter_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
        portfolio_grid = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        def selected_media(filter_name):
            if filter_name == "사진":
                return [item for item in portfolio_media if item["type"] == "photo"]
            if filter_name == "영상":
                return [item for item in portfolio_media if item["type"] == "video"]
            return portfolio_media

        def portfolio_tile(media, tile_w):
            is_video = media["type"] == "video"
            return ft.Container(
                width=tile_w,
                height=tile_w,
                border_radius=RADIUS_MD,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                bgcolor="#000000",
                content=ft.Stack(
                    controls=[
                        black_image_box(tile_w, tile_w, RADIUS_MD),
                        ft.Container(
                            left=7,
                            top=7,
                            padding=ft.padding.symmetric(horizontal=7, vertical=4),
                            bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                            border_radius=999,
                            content=ft.Text(media["tag"], size=9, color=TEXT_COLOR, weight=ft.FontWeight.W_600, max_lines=1),
                        ),
                        ft.Container(
                            right=8,
                            top=8,
                            visible=is_video,
                            content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED, size=20, color="#FFFFFF"),
                        ),
                        ft.Container(
                            left=0,
                            right=0,
                            bottom=0,
                            padding=ft.padding.symmetric(horizontal=8, vertical=8),
                            bgcolor=ft.Colors.with_opacity(0.62, "#000000"),
                            content=ft.Text(
                                media["title"],
                                size=10,
                                color="#FFFFFF",
                                weight=ft.FontWeight.W_600,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                    ],
                ),
            )

        def build_grid_controls(filter_name):
            items = selected_media(filter_name)
            tile_w = int((content_width() - 16) / 3)
            rows = []
            for index in range(0, len(items), 3):
                row_items = items[index:index + 3]
                controls = [portfolio_tile(item, tile_w) for item in row_items]
                while len(controls) < 3:
                    controls.append(ft.Container(width=tile_w, height=tile_w, opacity=0))
                rows.append(
                    ft.Row(
                        width=content_width(),
                        controls=controls,
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START,
                    )
                )
            return rows

        def portfolio_filter_chip(label):
            active = app_state.get("detail_portfolio_filter", "전체") == label

            def on_tap(e, selected=label):
                app_state["detail_portfolio_filter"] = selected
                filter_row.controls = [portfolio_filter_chip(name) for name in ["전체", "사진", "영상"]]
                portfolio_grid.controls = build_grid_controls(selected)
                filter_row.update()
                portfolio_grid.update()

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=on_tap,
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_500,
                ),
            )

        filter_row.controls = [portfolio_filter_chip(name) for name in ["전체", "사진", "영상"]]
        portfolio_grid.controls = build_grid_controls(portfolio_filter)

        content = ft.Column(
            controls=[
                page_header("아티스트 프로필", on_back=go_back),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=12, color="#10000000", offset=ft.Offset(0, 4)),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    black_image_box(78, 78, RADIUS_MD),
                                    ft.Column(
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text(artist["name"], size=20, weight=ft.FontWeight.W_800, color=TEXT_COLOR, expand=True),
                                                    ft.Container(
                                                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                                        bgcolor=MAIN_COLOR_SOFT,
                                                        border_radius=999,
                                                        content=ft.Text(artist["category"], size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                                    ),
                                                ],
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            ),
                                            ft.Text(f"{artist['job']} · {artist.get('distance', '')} · {artist.get('price', '')}", size=12, color=SUBTEXT_COLOR),
                                            ft.Text(artist["style"], size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                                        ],
                                        spacing=5,
                                        expand=True,
                                    ),
                                ],
                                spacing=14,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                            ft.Text(artist["intro"], size=13, color=SUBTEXT_COLOR, height=1.45),
                            ft.Row(
                                controls=[
                                    stat_block("포트폴리오", len(portfolio_media)),
                                    stat_block("리뷰", review_count),
                                    stat_block("평점", artist["rating"]),
                                ],
                                spacing=8,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=11, vertical=7),
                                        bgcolor=MAIN_COLOR_SOFT,
                                        border_radius=999,
                                        content=ft.Text(f"#{tag}", size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                                    )
                                    for tag in artist.get("tags", [])
                                ],
                                spacing=6,
                                wrap=True,
                            ),
                            ft.Row(
                                width=content_width() - SPACE_LG * 2,
                                controls=[
                                    ft.Container(on_click=save_click_local, content=save_button),
                                    ft.Container(
                                        width=92,
                                        height=48,
                                        border_radius=RADIUS_MD,
                                        bgcolor="#FFFFFF",
                                        border=ft.border.all(1, BORDER_COLOR),
                                        alignment=ft.Alignment(0, 0),
                                        on_click=message_click,
                                        ink=True,
                                        content=ft.Text("메시지", size=13, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                    ),
                                    ft.Container(
                                        expand=True,
                                        height=48,
                                        border_radius=RADIUS_MD,
                                        bgcolor=MAIN_COLOR,
                                        alignment=ft.Alignment(0, 0),
                                        on_click=reserve_click,
                                        ink=True,
                                        content=ft.Text("예약하기", size=13, color="#FFFFFF", weight=ft.FontWeight.W_800),
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=14,
                    ),
                ),
                ft.Container(height=14),
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
                                    ft.Column(
                                        controls=[
                                            ft.Text("포트폴리오", size=18, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                            ft.Text("사진과 영상으로 아티스트의 스타일을 확인해보세요.", size=12, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=3,
                                        expand=True,
                                    ),
                                    filter_row,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            portfolio_grid,
                        ],
                        spacing=14,
                    ),
                ),
                ft.Container(height=12),
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
                                    ft.Text("실제 리뷰", size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_800, expand=True),
                                    ft.Text(f"⭐ {artist['rating']}", size=13, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            review_card("FINDY 사용자", artist["category"], artist["reason"], rating=int(round(float(artist.get("rating", 5))))),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        render_phone_frame(content, None)

    await start_opening_flow()

if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR if os.path.isdir(ASSETS_DIR) else None)
