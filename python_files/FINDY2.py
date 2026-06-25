import asyncio
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
import calendar
import flet as ft

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.findy2_config import (
    ASSETS_DIR,
    FINDY2_AUTH_DATA_PATH,
    FINDY2_AUTH_API_URL,
    FINDY2_DEMO_LOGIN_ENABLED,
    FINDY2_DIRECT_MESSAGE_ENABLED,
    FINDY2_MEDIA_DIR,
    FINDY2_RESERVATION_ENABLED,
    FINDY2_SESSION_PATH,
    FINDY2_SOCIAL_AUTH_TIMEOUT_SECONDS,
    FINDY2_USER_DATA_PATH,
    RESERVATION_STORAGE_PATH,
    resolve_asset_file,
)
from core.findy2_state import create_findy2_state
from data.artists import BASE_ARTISTS
from data.categories import LEFT_OVERLAY_ICONS, SUBCATEGORIES
from data.findy2_content import (
    COMMUNITY_POST_TYPE_ORDER,
    default_community_posts,
    default_video_items,
    extract_metric,
    is_short_video,
)
from data.legal_content import LEGAL_DOCUMENTS, LEGAL_UPDATED_AT
from data.reviews import REVIEW_ITEMS
from data.review_safety import (
    LEGAL_RESPONSIBILITY_NOTICE,
    REVIEW_POLICY_NOTICE,
    REVIEW_REPORT_REASONS,
    REVIEW_STATUS_OPTIONS,
    SAFER_REVIEW_EXAMPLES,
    RISK_WARNING_MESSAGE,
    calculateRiskScore,
    detectReviewRisks,
    maskPersonalInfo,
    validateReviewBeforeSubmit,
)
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
from services.reservation_storage import (
    load_reservation_history,
    save_reservation_history,
)
from services.findy2_user_storage import (
    PERSISTED_KEYS,
    delete_findy2_user_data,
    load_findy2_user_data,
    save_findy2_user_data,
    user_scoped_data_path,
)
from services.findy2_auth import (
    AuthError,
    attach_verified_phone,
    authenticate_user,
    clear_session,
    create_session,
    delete_user,
    find_user_by_phone,
    find_usernames_by_phone,
    get_or_create_demo_user,
    read_remote_session_token,
    register_user,
    reset_password_by_phone,
    restore_session,
    social_login_or_register,
    update_user_profile,
)
from services.findy2_phone_auth import (
    PhoneAuthError,
    request_phone_otp,
    verify_phone_otp,
)
from services.findy2_media_storage import (
    MediaStorageError,
    delete_user_media,
    remove_media_file,
    store_images,
    store_video,
    validate_image_file,
    validate_video_file,
)
from services.findy2_social_auth import (
    SOCIAL_PROVIDERS,
    SocialAuthError,
    delete_social_account,
    social_auth_is_configured,
    start_social_auth,
    wait_for_social_auth,
)

async def main(page: ft.Page):

    def safe_go_back(e=None):
        try:
            go_back_page(e)
        except Exception:
            try:
                show_home_page()
            except Exception:
                pass
    def layout_metrics():
        page_width = getattr(page, "width", None) or PHONE_WIDTH
        frame_width = max(260, min(PHONE_WIDTH, page_width)) if page_width else PHONE_WIDTH
        target_content_width = max(CONTENT_WIDTH, 360)
        horizontal_gutter = 24 if frame_width < 340 else 40
        content_width = min(target_content_width, max(228, frame_width - horizontal_gutter))
        field_width = min(max(FIELD_WIDTH, 320), max(210, content_width - 24))
        half_card_width = max(104, int((content_width - SPACE_SM) / 2))
        return {
            "frame_width": frame_width,
            "content_width": content_width,
            "field_width": field_width,
            "half_card_width": half_card_width,
        }

    def preserve_snap_video_width():
        current_page = ""
        try:
            current_page = app_state.get("current_page", "")
        except NameError:
            current_page = ""
        return current_page in {"snap", "snap_detail", "write_snap", "video", "video_detail", "write_video"}

    def content_width():
        if preserve_snap_video_width():
            return min(CONTENT_WIDTH, layout_metrics()["content_width"])
        return layout_metrics()["content_width"]

    def field_width():
        if preserve_snap_video_width():
            return min(FIELD_WIDTH, layout_metrics()["field_width"])
        return layout_metrics()["field_width"]

    def half_card_width():
        if preserve_snap_video_width():
            return max(132, int((content_width() - SPACE_SM) / 2))
        return layout_metrics()["half_card_width"]

    def full_phone_width():
        return layout_metrics()["frame_width"]

    def full_phone_height():
        page_height = getattr(page, "height", None) or PHONE_HEIGHT
        return max(420, min(PHONE_HEIGHT, int(page_height - 20)))

    def default_header_back_handler(on_back=None):
        if on_back is not None:
            return on_back
        root_pages = {
            "opening",
            "login",
            "signup",
            "home",
            "home_category_transition",
            "category",
            "snap",
            "video",
            "my",
        }
        current = app_state.get("current_page", "")
        if current and current not in root_pages:
            return go_back_page
        return None

    def brand_title_header(title, on_back=None, width=None):
        header_width = width or content_width()
        back_handler = default_header_back_handler(on_back)
        clean_title = str(title or "").replace("FINDY ", "", 1).strip() or "FINDY"
        return ft.Container(
            width=header_width,
            height=48,
            content=ft.Stack(
                controls=[
                    ft.Container(
                        alignment=ft.Alignment(-1, 0),
                        visible=back_handler is not None,
                        content=ft.Container(
                            width=42,
                            height=42,
                            border_radius=21,
                            bgcolor=CARD_COLOR,
                            border=ft.border.all(1, BORDER_COLOR),
                            alignment=ft.Alignment(0, 0),
                            on_click=back_handler,
                            ink=True,
                            content=ft.Icon(app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"), size=21, color=TEXT_COLOR),
                        ),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(clean_title, size=24, color=TEXT_COLOR, weight=ft.FontWeight.W_900, text_align=ft.TextAlign.CENTER),
                    ),
                ],
            ),
        )

    def main_tab_header(title, actions=True, width=None):
        header_width = width or content_width()
        clean_title = str(title or "").replace("FINDY ", "", 1).strip()
        wordmark_path = resolve_asset_file("app_logo/app_findy_logo_wordmark.png")

        brand_control = (
            ft.Image(src=wordmark_path, width=104, height=31, fit=ft.ImageFit.CONTAIN)
            if wordmark_path
            else ft.Text("FINDY", size=28, color=MAIN_COLOR, weight=ft.FontWeight.W_900)
        )

        def action_icon(icon_names, on_click, tooltip):
            return ft.Container(
                width=38,
                height=38,
                border_radius=19,
                alignment=ft.Alignment(0, 0),
                on_click=on_click,
                ink=True,
                tooltip=tooltip,
                content=ft.Icon(app_icon(*icon_names), size=24, color=TEXT_COLOR),
            )

        action_controls = []
        if actions:
            action_controls = [
                action_icon(("SEARCH", "SEARCH_OUTLINED"), lambda e: show_search_page(), "검색"),
                action_icon(("SEND_OUTLINED", "NEAR_ME_OUTLINED"), lambda e: show_customer_messages_page(), "소식함"),
                action_icon(("NOTIFICATIONS_NONE", "NOTIFICATIONS_OUTLINED"), open_notifications_page, "알림"),
            ]

        return ft.Container(
            width=header_width,
            padding=ft.padding.only(top=4, bottom=10),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.72, BORDER_COLOR))),
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            brand_control,
                            ft.Text(clean_title, size=23, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ],
                        spacing=9,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                    ft.Container(expand=True),
                    *action_controls,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def build_standard_header(title, on_back=None, on_close=None, width=None):
        return brand_title_header(title, on_back=on_back, width=width or content_width())

    def page_header(title, on_back=None, width=None):
        return brand_title_header(title, on_back=on_back, width=width or content_width())

    def compose_top_bar(title, on_back, on_submit, submit_label="완료"):
        return ft.Container(
            width=content_width(),
            height=50,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=20,
                        alignment=ft.Alignment(0, 0),
                        on_click=on_back,
                        ink=True,
                        content=ft.Icon(app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"), size=22, color=TEXT_COLOR),
                    ),
                    ft.Text(title, size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True, text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        width=54,
                        height=38,
                        border_radius=19,
                        alignment=ft.Alignment(0, 0),
                        on_click=on_submit,
                        ink=True,
                        content=ft.Text(submit_label, size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_900),
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def compose_text_field(hint, multiline=False, min_lines=1, max_lines=1, size=15, weight=None):
        return ft.TextField(
            width=content_width(),
            hint_text=hint,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            border=ft.InputBorder.NONE,
            bgcolor=ft.Colors.TRANSPARENT,
            cursor_color=MAIN_COLOR,
            content_padding=ft.padding.symmetric(horizontal=0, vertical=6),
            text_style=ft.TextStyle(size=size, color=TEXT_COLOR, weight=weight),
            hint_style=ft.TextStyle(size=size, color=ft.Colors.with_opacity(0.48, SUBTEXT_COLOR), weight=weight),
        )

    def compose_bottom_action(icon_names, label, on_click=None):
        return ft.Container(
            height=38,
            padding=ft.padding.symmetric(horizontal=8),
            border_radius=12,
            on_click=on_click,
            ink=bool(on_click),
            content=ft.Row(
                controls=[
                    ft.Icon(app_icon(*icon_names), size=18, color=SUBTEXT_COLOR),
                    ft.Text(label, size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                ],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
        )

    def compose_bottom_toolbar(actions):
        return ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=4, vertical=8),
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.with_opacity(0.56, BORDER_COLOR))),
            content=ft.Row(
                controls=actions,
                spacing=6,
                scroll=ft.ScrollMode.HIDDEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def page_title_map():
        current_page = app_state.get("current_page", "")
        mapping = {
            "category": "커뮤니티",
            "snap": "스냅",
            "video": "비디오",
            "my": "내정보",
            "saved": "저장한 뷰티",
            "reservation": "예약",
            "reservation_confirm": "예약 확인",
            "reservation_complete": "예약 완료",
            "reservation_history": "예약내역",
            "notifications": "알림",
            "settings": "설정",
            "findy_recommendation": "FINDY 추천정보",
            "review": "리뷰",
            "review_admin": "운영 검토",
            "profile": "프로필",
            "edit_profile": "프로필 편집",
            "search": "검색",
            "search_results": "전체 보기",
            "snap_detail": "스냅",
            "support": "고객센터",
            "inquiry": "문의내역",
            "customer_messages": "소식함",
            "message_detail": "소식함 상세",
            "completed": "완료한 이용",
            "cancelled_treatments": "취소된 이용",
            "beauty_profile": "나의 FINDY",
            "notice": "공지사항",
            "feedback": "개선 의견",
            "placeholder_info": "안내",
            "my_content": "내가 쓴글",
            "saved_content": "저장",
            "liked_content": "좋아요",
            "content_detail": "상세",
            "community_board": "커뮤니티",
            "write_community": "글쓰기",
            "write_snap": "스냅 작성",
            "write_video": "비디오 작성",
            "video_detail": "비디오",
        }
        return mapping.get(current_page, "")

    def section_title(title, subtitle=None, on_click=None):
        return ui_section_title(title, subtitle=subtitle, on_click=on_click, width=content_width())

    def soft_button(label, bgcolor, text_color, on_click, border=None, width=None):
        return ui_soft_button(label, bgcolor, text_color, on_click, border=border, width=width or field_width())

    def review_card(name, category, review, photos=None, rating=5):
        return ui_review_card(name, category, review, width=content_width(), photos=photos, rating=rating)

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

    REVIEW_SERVICE_OPTIONS = [
        ("hair", "헤어"),
        ("nail", "네일아트"),
        ("makeup", "메이크업"),
        ("photo", "포토"),
        ("wedding", "웨딩"),
        ("tattoo", "반영구시술"),
        ("etc", "기타"),
    ]
    REVIEW_REVISIT_OPTIONS = [("yes", "예"), ("maybe", "고민 중"), ("no", "아니오")]

    def service_category_label(value):
        return dict(REVIEW_SERVICE_OPTIONS).get(value, value or "기타")

    def revisit_intent_label(value):
        return dict(REVIEW_REVISIT_OPTIONS).get(value, "고민 중")

    def public_profile_name(item):
        if not item:
            return "공개 표시명"
        return (
            item.get("displayName")
            or item.get("artistName")
            or item.get("nickname")
            or item.get("artist_name")
            or "공개 표시명"
        )

    def shop_display_name(item):
        if not item:
            return "FINDY 커뮤니티"
        return item.get("shopName") or item.get("shop_name") or item.get("shop") or "FINDY 커뮤니티"

    def review_identity(review):
        return review.get("id") or review.get("reservation_id") or f"review:{review.get('created_at', '')}:{review.get('artist_name', '')}"

    def review_visible_in_feed(review):
        return review.get("status", "visible") == "visible"

    def review_report_count(review_id):
        return len([report for report in app_state.get("review_reports", []) if report.get("reviewId") == review_id])

    def review_status_chip(status):
        colors = {
            "visible": (MAIN_COLOR_SOFT, MAIN_COLOR_DARK, "정상 노출"),
            "pending": ("#FFF7E8", "#9A6A1F", "검토 대기"),
            "hidden": ("#FFF1F1", "#B85C5C", "숨김"),
            "deleted": ("#EFEFEF", SUBTEXT_COLOR, "삭제"),
            "reported": ("#F7F1FF", "#7158A6", "신고됨"),
        }
        bg, fg, label = colors.get(status, colors["visible"])
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=9, vertical=5),
            bgcolor=bg,
            border_radius=999,
            content=ft.Text(label, size=10, color=fg, weight=ft.FontWeight.W_700),
        )

    def find_review_by_id(review_id):
        return next((review for review in app_state.get("written_reviews", []) if review.get("id") == review_id), None)

    def submitReview(review):
        validation = validateReviewBeforeSubmit(review)
        if not validation["canSubmit"]:
            raise ValueError(validation["message"] or "리뷰 제출 조건을 확인해주세요.")

        saved = dict(review)
        for field in ("visitPurpose", "positiveComment", "negativeComment", "reviewText"):
            saved[field] = maskPersonalInfo(saved.get(field, ""))
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        saved.setdefault("id", f"review_{len(app_state.get('written_reviews', [])) + 1}_{int(datetime.now().timestamp())}")
        saved.setdefault("userId", current_user_id())
        saved.setdefault("status", validation["status"])
        saved["riskScore"] = review.get("riskScore", validation["riskScore"])
        saved["detectedRiskTypes"] = review.get("detectedRiskTypes", validation["detectedRiskTypes"])
        saved.setdefault("createdAt", now)
        saved.setdefault("created_at", now.split(" ")[0])
        saved["updatedAt"] = now
        app_state.setdefault("written_reviews", []).append(saved)
        if not persist_user_data(notify_on_error=True):
            app_state["written_reviews"].remove(saved)
            return None
        return saved

    def reportReview(reviewId, reason, detail):
        report_count = len(app_state.get("review_reports", [])) + 1
        report = {
            "id": f"report_{report_count}_{int(datetime.now().timestamp())}",
            "reportId": f"report_{report_count}_{int(datetime.now().timestamp())}",
            "reviewId": reviewId,
            "reporterUserId": (app_state.get("current_user") or {}).get("id", "local_user"),
            "reason": reason,
            "detail": detail or "",
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "pending",
            "adminMemo": "",
            "resolvedAt": None,
        }
        app_state.setdefault("review_reports", []).append(report)
        if review_report_count(reviewId) >= 3:
            updateReviewStatus(reviewId, "hidden", "신고 3회 이상 누적으로 자동 숨김 처리")
        else:
            review = find_review_by_id(reviewId)
            if review and review.get("status") == "visible":
                review["status"] = "reported"
        persist_user_data()
        return report

    def updateReviewStatus(reviewId, status, adminMemo):
        if status not in REVIEW_STATUS_OPTIONS:
            raise ValueError("지원하지 않는 리뷰 상태입니다.")
        review = find_review_by_id(reviewId)
        if not review:
            return None
        review["status"] = status
        review["adminMemo"] = adminMemo or review.get("adminMemo", "")
        review["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        persist_user_data()
        return review

    def browse_result_card(item, on_click=None):
        return ui_browse_result_card(item, width=content_width(), on_click=on_click)

    def opening_visual():
        path = resolve_asset_file(OPENING_IMAGE)
        if path:
            return ft.Image(
                src=path,
                width=full_phone_width(),
                height=full_phone_height(),
                fit="contain",
                opacity=0,
                animate_opacity=ft.Animation(420, ft.AnimationCurve.EASE_IN_OUT),
            )
        return ft.Container(
            width=full_phone_width(),
            height=full_phone_height(),
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

    page.title = "FINDY"
    regular_font_rel = "Pretendard-Regular.ttf"
    bold_font_rel = "Pretendard-Bold.ttf"
    regular_font = os.path.join(ASSETS_DIR, "Pretendard-Regular.ttf")
    bold_font = os.path.join(ASSETS_DIR, "Pretendard-Bold.ttf")
    if not (os.path.exists(regular_font) and os.path.exists(bold_font)):
        regular_font_rel = "Pretendard/Pretendard-Regular.ttf"
        bold_font_rel = "Pretendard/Pretendard-Bold.ttf"
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

    app_state = create_findy2_state()

    def persist_user_data(notify_on_error=False):
        path = user_scoped_data_path(FINDY2_USER_DATA_PATH, current_user_id())
        saved = save_findy2_user_data(path, app_state)
        if not saved and notify_on_error:
            show_snack("사용자 데이터 저장에 실패했어요. 다시 시도해주세요.", bgcolor="#B85C5C")
        return saved

    def apply_authenticated_user(user):
        app_state["current_user"] = user
        saved_profile = dict(user.get("profile") or {})
        profile = dict(create_findy2_state().get("user_profile") or {})
        profile.update(saved_profile)
        profile["name"] = user.get("nickname") or profile.get("name") or "FINDY 회원"
        profile["username"] = profile["name"]
        profile["realName"] = user.get("realName") or profile.get("realName") or ""
        app_state["user_profile"] = profile

    def load_user_workspace(user):
        defaults = create_findy2_state()
        path = user_scoped_data_path(FINDY2_USER_DATA_PATH, (user or {}).get("id"))
        restored = load_findy2_user_data(path, defaults)
        if not restored and os.path.exists(os.path.expanduser(FINDY2_USER_DATA_PATH)):
            restored = load_findy2_user_data(FINDY2_USER_DATA_PATH, defaults)
            if restored:
                migration_state = dict(defaults)
                migration_state.update(restored)
                if save_findy2_user_data(path, migration_state):
                    try:
                        os.replace(
                            os.path.expanduser(FINDY2_USER_DATA_PATH),
                            os.path.expanduser(FINDY2_USER_DATA_PATH) + ".migrated",
                        )
                    except OSError:
                        pass
        for key in PERSISTED_KEYS:
            app_state[key] = restored.get(key, defaults.get(key))
        apply_authenticated_user(user)

    def clear_user_workspace():
        defaults = create_findy2_state()
        for key in PERSISTED_KEYS:
            app_state[key] = defaults.get(key)
        app_state["current_user"] = None

    restored_user = restore_session(FINDY2_AUTH_DATA_PATH, FINDY2_SESSION_PATH)
    if restored_user:
        load_user_workspace(restored_user)

    def current_user_id():
        return (app_state.get("current_user") or {}).get("id")

    def current_user_label():
        user = app_state.get("current_user") or {}
        return user.get("nickname") or user.get("username") or "FINDY 회원"

    def is_owned_by_current_user(item):
        item = item or {}
        source = item.get("source") if isinstance(item, dict) else None
        if isinstance(source, dict) and source is not item:
            return is_owned_by_current_user(source)
        owner_id = item.get("userId") or item.get("ownerUserId")
        return bool(owner_id and owner_id == current_user_id())

    def sync_profile_to_auth(profile):
        user_id = current_user_id()
        if not user_id:
            return True
        try:
            updated_user = update_user_profile(FINDY2_AUTH_DATA_PATH, user_id, profile)
        except AuthError as error:
            show_snack(str(error), bgcolor="#B85C5C")
            return False
        apply_authenticated_user(updated_user)
        return True

    subcategories = SUBCATEGORIES

    beauty_filter_labels = ["전체", "헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
    content_category_entries = [
        {
            "key": "리뷰",
            "label": "리뷰",
            "icon": "RATE_REVIEW",
            "description": "시술 경험과 후기를 먼저 보기",
        },
        {
            "key": "커뮤니티",
            "label": "커뮤니티",
            "icon": "FORUM",
            "description": "리뷰, 공유, 질문을 한곳에서 보기",
        },
        {
            "key": "자유게시판",
            "label": "자유게시판",
            "icon": "CHAT_BUBBLE_OUTLINE",
            "description": "뷰티 수다와 고민을 자유롭게 보기",
        },
        {
            "key": "스냅",
            "label": "스냅",
            "icon": "PHOTO_LIBRARY",
            "description": "사진 중심 스타일 참고 보기",
        },
        {
            "key": "비디오",
            "label": "비디오",
            "icon": "SMART_DISPLAY",
            "description": "짧은 팁 영상을 이어서 보기",
        },
    ]
    content_category_keys = {item["key"] for item in content_category_entries}
    left_overlay_categories = {
        item["key"]: beauty_filter_labels
        for item in content_category_entries
    }

    left_overlay_icons = {
        **LEFT_OVERLAY_ICONS,
        **{item["key"]: item["icon"] for item in content_category_entries},
    }

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
        persist_user_data()

    def is_saved(artist_id):
        return artist_id in app_state["saved_ids"]

    def show_snack(message, bgcolor=None):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white", size=13, weight=ft.FontWeight.W_700),
            bgcolor=bgcolor or MAIN_COLOR,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.symmetric(horizontal=18, vertical=18),
            duration=2200,
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

    def seed_message_threads():
        threads = app_state.setdefault("message_threads", [])
        if threads:
            return threads

        threads.append(
            {
                "id": "msg_seed_1",
                "room_id": "findy_team",
                "room_name": "FINDY 소식",
                "room_category": "커뮤니티",
                "customer_name": "김수아",
                "category": "비디오 팁",
                "status": "안내",
                "updated_at": "오늘 10:20",
                "messages": [
                    {
                        "sender": "system",
                        "text": "나만의 뷰티 팁을 1분 이내 비디오로 올려보세요. 비디오 화면에서 바로 시작할 수 있어요.",
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

    def find_message_thread_by_room(room_id):
        if not room_id:
            return None
        return next(
            (thread for thread in current_message_threads() if thread.get("room_id") == room_id),
            None,
        )

    def open_message_thread(thread_id, back_target=None):
        app_state["active_message_thread_id"] = thread_id
        app_state["message_reply_draft"] = ""
        app_state["message_back_target"] = back_target or app_state.get("current_page")
        app_state["current_page"] = "message_detail"
        render_current_page()

    def start_customer_chat_with_room(room, back_target="customer_messages"):
        room_id = room.get("id") or room.get("room_id")
        existing_thread = find_message_thread_by_room(room_id)
        if existing_thread:
            open_message_thread(existing_thread.get("id"), back_target)
            return
        show_customer_messages_page()

    def append_thread_message(thread, sender, text):
        thread.setdefault("messages", []).append(
            {
                "sender": sender,
                "text": text,
                "time": datetime.now().strftime("%H:%M"),
            }
        )
        thread["updated_at"] = "방금 전"
        thread["status"] = "확인 완료" if sender == "system" else "전송 완료"

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
            "service": services[0] if services else "기본 서비스",
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
            normalized["service"] = normalized.get("category") or "기본 서비스"
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
            "service": form.get("service", "기본 서비스"),
            "date": form.get("date"),
            "time": form.get("time"),
            "note": form.get("note", ""),
            "status": "예약 완료",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    def save_reservation_history_to_file():
        return save_reservation_history(
            RESERVATION_STORAGE_PATH,
            app_state.get("reservation_history", []),
        )

    def load_reservation_history_from_file():
        return load_reservation_history(
            RESERVATION_STORAGE_PATH,
            normalize_reservation_history_item,
        )

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
        clear_session(FINDY2_SESSION_PATH)
        clear_user_workspace()
        app_state["selected_tab"] = 2
        app_state["page_history"] = []
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

    def open_account_deletion_dialog(e=None):
        user = app_state.get("current_user") or {}
        if not user:
            show_snack("로그인된 계정을 찾을 수 없어요.", bgcolor="#B85C5C")
            return

        is_social_account = user.get("provider", "email") != "email"
        password_field = ft.TextField(
            label="현재 비밀번호",
            password=True,
            can_reveal_password=True,
            autofocus=True,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
        )
        confirmation_field = ft.TextField(
            label="'계정 삭제'를 입력해주세요",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
        )

        def close_dialog(event=None):
            if page.dialog:
                page.dialog.open = False
                page.update()

        def finish_account_deletion(user_id):
            data_path = user_scoped_data_path(FINDY2_USER_DATA_PATH, user_id)
            data_deleted = delete_findy2_user_data(data_path)
            media_deleted = delete_user_media(FINDY2_MEDIA_DIR, user_id)
            clear_session(FINDY2_SESSION_PATH)
            close_dialog()
            clear_user_workspace()
            app_state["selected_tab"] = 2
            app_state["page_history"] = []
            app_state["current_page"] = "login"
            if not data_deleted or not media_deleted:
                show_snack(
                    "계정은 삭제됐지만 일부 로컬 파일 정리가 필요해요.",
                    bgcolor="#B85C5C",
                )
            show_login_page()

        def validate_confirmation():
            if confirmation_field.value.strip() != "계정 삭제":
                show_snack("'계정 삭제'를 정확히 입력해주세요.", bgcolor="#B85C5C")
                return False
            return True

        def confirm_email_delete(event=None):
            if not validate_confirmation():
                return
            user_id = user.get("id")
            try:
                delete_user(
                    FINDY2_AUTH_DATA_PATH,
                    user_id,
                    password_field.value,
                )
            except AuthError as error:
                show_snack(str(error), bgcolor="#B85C5C")
                return
            finish_account_deletion(user_id)

        async def confirm_social_delete(event=None):
            if not validate_confirmation():
                return
            remote_token = read_remote_session_token(FINDY2_SESSION_PATH)
            try:
                await delete_social_account(
                    FINDY2_AUTH_API_URL,
                    remote_token,
                )
                delete_user(
                    FINDY2_AUTH_DATA_PATH,
                    user.get("id"),
                    verified_social=True,
                )
            except (AuthError, SocialAuthError) as error:
                show_snack(str(error), bgcolor="#B85C5C")
                return
            finish_account_deletion(user.get("id"))

        dialog_controls = [
            ft.Text(
                (
                    "FINDY 통합회원과 이 기기의 작성글, 댓글, 좋아요, 저장, 프로필, 업로드 파일을 모두 삭제합니다."
                    if is_social_account
                    else "작성한 글, 댓글, 좋아요, 저장, 프로필과 업로드 파일이 이 기기에서 모두 삭제되며 복구할 수 없습니다."
                ),
                size=12,
                color=SUBTEXT_COLOR,
            ),
        ]
        if not is_social_account:
            dialog_controls.append(password_field)
        dialog_controls.append(confirmation_field)

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("계정을 삭제할까요?", weight=ft.FontWeight.W_900),
            content=ft.Container(
                width=min(360, content_width() - 48),
                content=ft.Column(
                    controls=dialog_controls,
                    spacing=14,
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton("취소", on_click=close_dialog),
                ft.TextButton(
                    "영구 삭제",
                    style=ft.ButtonStyle(color="#B85C5C"),
                    on_click=(
                        lambda event: page.run_task(confirm_social_delete, event)
                        if is_social_account
                        else confirm_email_delete(event)
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog.open = True
        page.update()

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
                    "review_admin",
                    "my_content",
                    "saved_content",
                    "liked_content",
                    "settings",
                    "connected_accounts",
                    "findy_recommendation",
                    "content_detail",
                    "completed",
                    "beauty_profile",
                    "notice",
                    "feedback",
                    "support",
                    "inquiry",
                    "notifications",
                    "legal",
                }:
                    app_state["selected_tab"] = 4
                render_current_page()
                return

        app_state["_suppress_next_history_record"] = True
        app_state["current_page"] = "home"
        app_state["selected_tab"] = 2
        show_home_page()

    def _render_current_page_unchecked():
        page_name = app_state.get("current_page", "home")
        if page_name == "opening":
            show_opening_page()
        elif page_name == "login":
            show_login_page()
        elif page_name == "signup":
            show_signup_page("user")
        elif page_name == "account_recovery":
            show_account_recovery_page(app_state.get("account_recovery_mode", "find_id"))
        elif page_name == "phone_onboarding":
            show_phone_onboarding_page()
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
        elif page_name == "beauty_category_page":
            show_beauty_category_page(app_state.get("selected_beauty_category", "헤어"))
        elif page_name == "search_results":
            show_search_results_page()
        elif page_name == "my":
            show_my_page()
        elif page_name == "profile":
            show_profile_page()
        elif page_name == "edit_profile":
            show_edit_profile_page()
        elif page_name == "saved":
            show_saved_page()
        elif page_name == "detail":
            show_detail_page()
        elif page_name == "reservation_history":
            open_reservation_entry()
        elif page_name == "cancelled_treatments":
            show_cancelled_treatments_page()
        elif page_name == "my_reviews":
            show_my_reviews_page()
        elif page_name == "review":
            show_review_page()
        elif page_name == "write_review":
            show_write_review_page()
        elif page_name == "review_admin":
            show_review_admin_page()
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
        elif page_name == "liked_content":
            show_liked_content_page()
        elif page_name == "settings":
            show_settings_page()
        elif page_name == "connected_accounts":
            show_connected_accounts_page()
        elif page_name == "legal":
            show_legal_page()
        elif page_name == "findy_recommendation":
            show_findy_recommendation_page()
        elif page_name == "content_detail":
            show_content_detail_page()
        elif page_name == "reservation":
            show_reservation_page() if FINDY2_RESERVATION_ENABLED else show_future_reservation_page()
        elif page_name == "reservation_confirm":
            show_reservation_confirm_page() if FINDY2_RESERVATION_ENABLED else show_future_reservation_page()
        elif page_name == "reservation_complete":
            show_reservation_complete_page() if FINDY2_RESERVATION_ENABLED else show_future_reservation_page()
        elif page_name == "notifications":
            show_notification_page()
        elif page_name == "support":
            show_support_page()
        elif page_name == "inquiry":
            show_inquiry_page()
        elif page_name == "customer_messages":
            show_customer_messages_page()
        elif page_name == "message_detail":
            show_message_detail_page()
        elif page_name == "community_board":
            show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 2))
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

    public_pages = {"opening", "login", "signup", "account_recovery", "phone_onboarding"}

    def show_runtime_error_page(error=None):
        if error is not None:
            print(f"FINDY2 runtime error: {error}")
        failed_page = app_state.get("current_page", "home")

        def retry(e=None):
            app_state["current_page"] = failed_page
            render_current_page()

        def return_home(e=None):
            app_state["current_page"] = "home"
            app_state["selected_tab"] = 2
            render_current_page()

        compact_error_layout = full_phone_width() < 330
        error_actions = [
            soft_button("다시 시도", MAIN_COLOR, "#FFFFFF", retry, width=126 if not compact_error_layout else 180),
            soft_button("홈으로", CHIP_BG, TEXT_COLOR, return_home, width=126 if not compact_error_layout else 180),
        ]
        page.clean()
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                bgcolor=BG_COLOR,
                content=ft.Container(
                    width=min(340, full_phone_width() - 32),
                    padding=ft.padding.symmetric(horizontal=24, vertical=28),
                    bgcolor="#FFFFFF",
                    border_radius=26,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Icon(app_icon("ERROR_OUTLINE", "INFO_OUTLINE"), size=34, color=MAIN_COLOR),
                            ft.Text("화면을 불러오지 못했어요", size=19, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                            ft.Text("입력한 내용은 유지했어요. 다시 시도하거나 홈으로 이동해주세요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                            (
                                ft.Column(
                                    controls=error_actions,
                                    spacing=8,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                )
                                if compact_error_layout
                                else ft.Row(
                                    controls=error_actions,
                                    spacing=8,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                )
                            ),
                        ],
                        spacing=14,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            )
        )
        page.update()

    def render_current_page():
        page_name = app_state.get("current_page", "home")
        if page_name not in public_pages and not app_state.get("current_user"):
            app_state["current_page"] = "login"
            app_state["page_history"] = []
        try:
            _render_current_page_unchecked()
        except Exception as error:
            show_runtime_error_page(error)

    def go_category_page(e=None):
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 0
        app_state["community_category_filter"] = "전체"
        app_state["community_board_type"] = "자유"
        app_state["current_page"] = "community_board"
        show_community_board_page("자유", selected_tab=0)

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

        for category_name, items in subcategories.items():
            if matches_query(query, category_name, " ".join(items)):
                results.append({
                    "type": "category",
                    "title": category_name,
                    "subtitle": "카테고리",
                    "meta": "관련 커뮤니티 글과 비디오 팁을 둘러볼 수 있어요.",
                    "description": f"{category_name} 관련 리뷰, 질문, 공유글과 비디오 팁을 찾아볼 수 있어요.",
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

        for video in get_all_video_items():
            if matches_query(query, video.get("title"), video.get("subtitle"), video.get("category")):
                results.append({
                    "type": "video",
                    "category": video.get("category", "비디오"),
                    "title": video.get("title", "비디오 팁"),
                    "subtitle": video.get("subtitle", "FINDY 회원의 뷰티 팁"),
                    "meta": f"{video.get('duration', '0:59')} · 조회 {video.get('views', '0')}",
                    "description": "회원이 공유한 짧은 비디오 팁이에요.",
                    "badge": "비디오",
                    "source": video,
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
                for post in community_posts()
                if normalize_overlay_category_name(post.get("category")) == normalized_category
            ]
            return user_posts

        return []

    def show_write_community_page():
        close_overlays()
        app_state["current_page"] = "write_community"
        selected_type = [app_state.get("community_write_type", "질문")]
        selected_category = [app_state.get("community_category_filter", "전체")]
        if selected_category[0] == "전체":
            selected_category[0] = app_state.get("selected_category") or "헤어"
        if selected_type[0] == "전체":
            selected_type[0] = "질문"

        type_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
        category_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
        selected_topic_text = ft.Text("", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True)

        def refresh_write_chips():
            selected_topic_text.value = f"{selected_type[0]} · {selected_category[0]}"
            type_row.controls = [
                community_chip(
                    label,
                    selected_type[0] == label,
                    lambda e, value=label: (
                        selected_type.__setitem__(0, value),
                        refresh_write_chips(),
                        page.update(),
                    ),
                )
                for label in ["리뷰", "공유", "질문", "자유"]
            ]
            category_row.controls = [
                community_chip(
                    label,
                    selected_category[0] == label,
                    lambda e, value=label: (
                        selected_category.__setitem__(0, value),
                        refresh_write_chips(),
                        page.update(),
                    ),
                )
                for label in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
            ]

        refresh_write_chips()

        title_field = compose_text_field("제목을 입력해주세요.", size=20, weight=ft.FontWeight.W_900)
        content_field = compose_text_field(
            "궁금한 점, 시술 경험, 전후 이야기, 뷰티 수다를 자유롭게 작성해보세요.\n#헤어 #네일아트 #메이크업...",
            multiline=True,
            min_lines=11,
            max_lines=16,
            size=14,
        )
        extra_field = compose_text_field("사용 제품, 가격대, 참고 정보나 태그를 추가해보세요. (선택)", size=13)
        selected_photos = []
        photo_count_text = ft.Text("0/6", size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700)
        photos_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
        photos_preview = ft.Container(width=content_width() - 36, visible=False, content=photos_row)

        def refresh_community_photo_preview():
            photos_row.controls.clear()
            for index, path in enumerate(selected_photos):
                def remove_photo(e=None, target_index=index):
                    selected_photos.pop(target_index)
                    refresh_community_photo_preview()

                photos_row.controls.append(
                    ft.Stack(
                        width=76,
                        height=76,
                        controls=[
                            ft.Image(src=path, width=76, height=76, fit=ft.ImageFit.COVER, border_radius=12),
                            ft.Container(
                                right=4,
                                top=4,
                                width=22,
                                height=22,
                                border_radius=11,
                                bgcolor=ft.Colors.with_opacity(0.72, "#000000"),
                                alignment=ft.Alignment(0, 0),
                                ink=True,
                                on_click=remove_photo,
                                content=ft.Icon(app_icon("CLOSE"), size=13, color="#FFFFFF"),
                            ),
                        ],
                    )
                )
            photos_preview.visible = bool(selected_photos)
            photo_count_text.value = f"{len(selected_photos)}/6"
            page.update()

        def on_community_photos_picked(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            remaining = 6 - len(selected_photos)
            for selected_file in e.files[:remaining]:
                if not selected_file.path:
                    continue
                try:
                    validate_image_file(selected_file.path)
                except MediaStorageError as error:
                    show_snack(str(error), bgcolor="#B85C5C")
                    continue
                if selected_file.path not in selected_photos:
                    selected_photos.append(selected_file.path)
            refresh_community_photo_preview()
            if len(e.files) > remaining:
                show_snack("커뮤니티 사진은 최대 6장까지 등록할 수 있어요.", bgcolor="#B85C5C")

        community_photo_picker = ft.FilePicker(on_result=on_community_photos_picked)
        page.overlay.append(community_photo_picker)
        page.update()

        def pick_community_photos(e=None):
            if len(selected_photos) >= 6:
                show_snack("커뮤니티 사진은 최대 6장까지 등록할 수 있어요.", bgcolor="#B85C5C")
                return
            community_photo_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "gif"],
            )

        def go_back(e=None):
            if community_photo_picker in page.overlay:
                page.overlay.remove(community_photo_picker)
            show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 2))

        def submit_post(e):
            title = (title_field.value or "").strip()
            body_text = (content_field.value or "").strip()
            extra_text = (extra_field.value or "").strip()
            if not title:
                show_snack("글 제목을 입력해주세요.", bgcolor="#B85C5C")
                return
            if not body_text:
                show_snack("글 내용을 입력해주세요.", bgcolor="#B85C5C")
                return

            try:
                stored_images = store_images(
                    selected_photos,
                    FINDY2_MEDIA_DIR,
                    current_user_id(),
                    limit=6,
                )
            except MediaStorageError as error:
                show_snack(str(error), bgcolor="#B85C5C")
                return

            new_post = {
                "id": f"community_user_{int(datetime.now().timestamp())}",
                "userId": current_user_id(),
                "type": "community",
                "post_type": selected_type[0],
                "title": title,
                "subtitle": f"{current_user_label()} · {selected_category[0]} · 방금 전",
                "meta": "댓글 0 · 저장 0",
                "description": body_text if not extra_text else f"{body_text}\n\n{extra_text}",
                "badge": selected_type[0],
                "category": selected_category[0],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "tags": [selected_category[0], selected_type[0], "새글"],
                "photos": [item["path"] for item in stored_images],
                "imageMetadata": stored_images,
            }
            app_state.setdefault("community_posts", []).insert(0, new_post)
            if not persist_user_data(notify_on_error=True):
                app_state["community_posts"].remove(new_post)
                for stored_image in stored_images:
                    remove_media_file(stored_image.get("path"), FINDY2_MEDIA_DIR)
                return
            if community_photo_picker in page.overlay:
                page.overlay.remove(community_photo_picker)
            app_state["community_board_type"] = selected_type[0]
            app_state["community_category_filter"] = selected_category[0]
            app_state["selected_subcategory"] = "커뮤니티"
            app_state["search_results"] = filtered_community_posts(selected_type[0], selected_category[0])
            app_state["category_browse_mode"] = True
            open_completion_feedback(
                f"{selected_type[0]} 글이 등록되었어요",
                "작성한 글은 커뮤니티 게시판에서 바로 확인할 수 있어요.",
                "게시판 보기",
                "community_board",
                selected_tab=1 if selected_type[0] == "공유" else 3 if selected_type[0] == "질문" else 2,
                icon_name="FORUM",
            )

        topic_sheet = ft.Container(
            width=content_width(),
            visible=False,
            padding=ft.padding.symmetric(horizontal=18, vertical=18),
            bgcolor="#FFFFFF",
            border_radius=ft.border_radius.only(top_left=26, top_right=26, bottom_left=20, bottom_right=20),
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Text("게시글 주제를 선택해주세요.", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                    ft.Row(
                        controls=[
                            ft.Icon(app_icon("FORUM", "CHAT_BUBBLE_OUTLINE"), size=20, color=MAIN_COLOR),
                            ft.Text("글 종류", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    type_row,
                    ft.Row(
                        controls=[
                            ft.Icon(app_icon("AUTO_AWESOME", "TUNE"), size=20, color=MAIN_COLOR),
                            ft.Text("뷰티 분야", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    category_row,
                ],
                spacing=12,
            ),
        )

        def toggle_topic_sheet(e=None):
            topic_sheet.visible = not topic_sheet.visible
            page.update()

        topic_selector = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=0, vertical=11),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.58, BORDER_COLOR))),
            on_click=toggle_topic_sheet,
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Text("주제", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                    selected_topic_text,
                    ft.Icon(app_icon("KEYBOARD_ARROW_DOWN", "EXPAND_MORE"), size=20, color=MAIN_COLOR_DARK),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        editor_panel = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            bgcolor="#FFFFFF",
            border_radius=26,
            border=ft.border.all(1, ft.Colors.with_opacity(0.52, BORDER_COLOR)),
            content=ft.Column(
                controls=[
                    topic_selector,
                    topic_sheet,
                    title_field,
                    content_field,
                    extra_field,
                    photos_preview,
                    compose_bottom_toolbar([
                        compose_bottom_action(("IMAGE_OUTLINED", "PHOTO_LIBRARY_OUTLINED"), "사진", pick_community_photos),
                        compose_bottom_action(("PLACE_OUTLINED", "LOCATION_ON_OUTLINED"), "장소", lambda e: show_snack("장소 첨부는 곧 연결될 예정이에요.")),
                        compose_bottom_action(("HOW_TO_VOTE_OUTLINED", "BALLOT_OUTLINED"), "투표", lambda e: show_snack("투표 기능은 곧 연결될 예정이에요.")),
                        compose_bottom_action(("TAG", "NUMBERS"), "태그", lambda e: show_snack("내용에 #태그를 입력해보세요.")),
                        ft.Container(expand=True),
                        photo_count_text,
                    ]),
                ],
                spacing=6,
            ),
        )

        body = ft.Column(
            controls=[
                compose_top_bar("커뮤니티 글쓰기", go_back, submit_post),
                editor_panel,
                ft.Container(height=24),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def community_posts():
        user_posts = [post.copy() for post in app_state.get("community_posts", [])]
        default_posts = []
        for idx, post in enumerate(default_community_posts(), start=1):
            copied = post.copy()
            copied.setdefault("id", f"community_seed_{idx}")
            default_posts.append(copied)
        return user_posts + default_posts

    def community_post_type(item):
        return item.get("post_type") or item.get("badge") or item.get("type") or "자유"

    def community_type_rank(item):
        return COMMUNITY_POST_TYPE_ORDER.get(community_post_type(item), 99)

    def community_popularity_score(item):
        meta = item.get("meta", "")
        return (
            extract_metric(meta, "좋아요")
            + extract_metric(meta, "댓글")
            + extract_metric(meta, "저장")
        )

    def filtered_community_posts(board_type=None, category=None):
        board_type = board_type or app_state.get("community_board_type", "자유")
        category = category or app_state.get("community_category_filter", "전체")
        items = community_posts()
        if board_type == "리뷰":
            known_ids = {str(item.get("id")) for item in items}
            for review in review_feed_items():
                review_id = str(review_identity(review))
                if review_id in known_ids:
                    continue
                rating = float(review.get("rating", 5) or 5)
                review_category = service_category_label(
                    review.get("serviceCategory") or review.get("category")
                )
                items.append(
                    {
                        "id": review_id,
                        "type": "community",
                        "post_type": "리뷰",
                        "category": review_category,
                        "title": review.get("reviewTitle")
                        or review.get("shopName")
                        or "서비스 이용 후기",
                        "subtitle": (
                            f'{public_profile_name(review)} · FINDY · '
                            f'{review.get("created_at", review.get("createdAt", "추천 리뷰"))}'
                        ),
                        "meta": (
                            f"만족도 {rating:.1f} · 댓글 {max(1, review_report_count(review_id))} "
                            f"· 저장 {max(1, int(rating * 4))}"
                        ),
                        "description": review.get("reviewText")
                        or review.get("content")
                        or "",
                        "badge": "리뷰",
                        "rating": rating,
                        "verifiedVisit": bool(review.get("verifiedVisit")),
                        "tags": [
                            tag
                            for tag in [
                                review_category,
                                "인증된 방문" if review.get("verifiedVisit") else "비인증",
                            ]
                            if tag
                        ],
                        "source": review,
                        "source_type": "review",
                    }
                )
        if board_type == "인기":
            items = [
                item
                for item in items
                if item.get("post_type", item.get("badge")) in {"자유", "리뷰", "질문"}
            ]
        elif board_type != "전체":
            items = [item for item in items if item.get("post_type", item.get("badge")) == board_type]
        if category != "전체":
            normalized = normalize_overlay_category_name(category)
            items = [
                item
                for item in items
                if normalize_overlay_category_name(item.get("category")) == normalized
            ]
        sort_mode = app_state.get("community_sort_mode", "popular")
        if board_type == "인기":
            return sorted(items, key=community_popularity_score, reverse=True)
        if sort_mode == "latest":
            return items
        if sort_mode == "comment":
            return sorted(items, key=lambda item: extract_metric(item.get("meta", ""), "댓글"), reverse=True)
        return sorted(
            items,
            key=community_popularity_score,
            reverse=True,
        )

    def community_chip(label, active, on_click):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            bgcolor=MAIN_COLOR if active else CHIP_BG,
            border_radius=999,
            border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
            on_click=on_click,
            ink=True,
            content=ft.Text(
                label,
                size=12,
                color="#FFFFFF" if active else TEXT_COLOR,
                weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_500,
            ),
        )

    def community_type_icon(board_type):
        mapping = {
            "리뷰": ("RATE_REVIEW_OUTLINED", "RATE_REVIEW"),
            "스냅": ("PHOTO_LIBRARY_OUTLINED", "PHOTO_LIBRARY"),
            "비디오": ("SMART_DISPLAY_OUTLINED", "SMART_DISPLAY"),
            "질문": ("HELP_OUTLINE", "CONTACT_SUPPORT_OUTLINED"),
            "자유": ("FORUM_OUTLINED", "CHAT_BUBBLE_OUTLINE"),
        }
        names = mapping.get(board_type, ("AUTO_AWESOME_MOSAIC_OUTLINED", "FORUM_OUTLINED"))
        return app_icon(*names)

    def community_author_meta(item):
        subtitle = item.get("subtitle") or ""
        parts = [part.strip() for part in subtitle.split("·") if part.strip()]
        author = parts[0] if parts else item.get("author", "FINDY 회원")
        area = parts[1] if len(parts) > 1 else item.get("area", "FINDY")
        time_text = parts[2] if len(parts) > 2 else item.get("created_at", item.get("createdAt", "방금 전"))
        return author, area, time_text

    def compact_metric_text(item):
        meta = item.get("meta", "")
        views = extract_metric(meta, "조회")
        likes = extract_metric(meta, "좋아요") or extract_metric(meta, "만족도")
        comments = extract_metric(meta, "댓글")
        saves = extract_metric(meta, "저장")
        left = []
        if views:
            left.append(f"조회 {views:,}")
        if saves and not views:
            left.append(f"저장 {saves:,}")
        right = []
        if likes:
            right.append(("THUMB_UP_OUTLINED", f"{likes:,}"))
        if comments:
            right.append(("CHAT_BUBBLE_OUTLINE", f"{comments:,}"))
        return " · ".join(left), right

    def community_mini_badge(text, on_click=None, selected=False):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=9, vertical=5),
            bgcolor=MAIN_COLOR if selected else ft.Colors.with_opacity(0.66, CHIP_BG),
            border_radius=999,
            border=ft.border.all(1, MAIN_COLOR if selected else ft.Colors.with_opacity(0.55, BORDER_COLOR)),
            on_click=on_click,
            ink=on_click is not None,
            content=ft.Text(
                text,
                size=10,
                color="#FFFFFF" if selected else MAIN_COLOR_DARK,
                weight=ft.FontWeight.W_800,
            ),
        )

    def community_result_card(item, back_page="search_results"):
        display = item.copy()
        display["title"] = item.get("title", "커뮤니티 글")
        display["subtitle"] = item.get("subtitle", item.get("category", "커뮤니티"))
        display["badge"] = item.get("post_type", item.get("badge", "커뮤니티"))

        def open_item(e=None):
            app_state["content_detail_back_page"] = back_page
            open_content_detail(display, back_page=back_page)

        author, area, time_text = community_author_meta(display)
        metric_left, metric_right = compact_metric_text(display)
        detail_meta = " · ".join([part for part in [area, time_text] if part])
        stat_text = metric_left or display.get("meta", "")
        avatar_label = (author or "F")[0].upper()
        description_text = (display.get("description") or "").strip()
        is_review = display.get("badge") == "리뷰" or display.get("post_type") == "리뷰"
        raw_rating = display.get("rating")
        if raw_rating is None and is_review:
            satisfaction = str(display.get("meta", "")).split("만족도", 1)
            try:
                raw_rating = float(satisfaction[1].strip().split(" ", 1)[0]) if len(satisfaction) > 1 else 5.0
            except (TypeError, ValueError):
                raw_rating = 5.0
        rating = max(0.0, min(5.0, float(raw_rating or 0))) if is_review else 0.0

        def filter_review_type(e=None):
            app_state["community_board_type"] = "리뷰"
            app_state["community_category_filter"] = "전체"
            show_community_board_page("리뷰", selected_tab=0)

        def filter_review_category(e=None):
            app_state["community_board_type"] = "리뷰"
            app_state["community_category_filter"] = display.get("category", "전체")
            show_community_board_page("리뷰", selected_tab=0)

        tag_controls = [
            community_mini_badge(tag)
            for tag in display.get("tags", [])[:3]
        ]
        body_controls = [
            ft.Text(display.get("title", "제목 없음"), size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_900, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        ]
        if description_text:
            body_controls.append(
                ft.Text(description_text, size=12, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, height=1.25)
            )
        if is_review:
            body_controls.append(
                ft.Row(
                    controls=[
                        community_mini_badge("리뷰", filter_review_type, selected=True),
                        community_mini_badge(display.get("category", "전체"), filter_review_category),
                        ft.Container(expand=True),
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.STAR_ROUNDED if index < int(round(rating)) else ft.Icons.STAR_BORDER_ROUNDED,
                                    size=14,
                                    color=MAIN_COLOR if index < int(round(rating)) else BORDER_COLOR,
                                )
                                for index in range(5)
                            ],
                            spacing=0,
                        ),
                        ft.Text(
                            f"{rating:.1f}",
                            size=11,
                            color=MAIN_COLOR_DARK,
                            weight=ft.FontWeight.W_900,
                        ),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        if tag_controls:
            body_controls.append(
                ft.Row(
                    controls=[
                        *([] if is_review else [community_mini_badge(display.get("category", "커뮤니티"))]),
                        *tag_controls,
                    ],
                    spacing=6,
                    wrap=True,
                )
            )
        return ft.Container(
            width=content_width(),
            padding=ft.padding.only(left=14, right=14, top=12, bottom=8),
            bgcolor=CARD_COLOR,
            border_radius=23,
            border=ft.border.all(1, ft.Colors.with_opacity(0.78, BORDER_COLOR)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color="#08000000",
                offset=ft.Offset(0, 4),
            ),
            ink=True,
            on_click=open_item,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=38,
                                height=38,
                                border_radius=19,
                                bgcolor=ft.Colors.with_opacity(0.72, CHIP_BG),
                                border=ft.border.all(1, BORDER_COLOR),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(avatar_label, size=15, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_900),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(author, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(detail_meta, size=11, color=SUBTEXT_COLOR, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            (
                                ft.Container(width=0)
                                if is_review
                                else community_mini_badge(display.get("badge", "글"))
                            ),
                            ft.Container(
                                width=30,
                                height=30,
                                border_radius=15,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon("MORE_VERT", "MORE_HORIZ"), size=18, color=ft.Colors.with_opacity(0.72, SUBTEXT_COLOR)),
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    *body_controls,
                    ft.Container(height=1, bgcolor=ft.Colors.with_opacity(0.34, BORDER_COLOR)),
                    ft.Container(
                        height=17,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Row(
                            controls=[
                                ft.Text(stat_text, size=10, color=SUBTEXT_COLOR, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                *[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=4, vertical=0),
                                        bgcolor=ft.Colors.TRANSPARENT,
                                        border_radius=999,
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(app_icon(icon), size=12, color=MAIN_COLOR_DARK),
                                                ft.Text(value, size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                            ],
                                            spacing=2,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                            tight=True,
                                        ),
                                    )
                                    for icon, value in metric_right
                                ],
                            ],
                            spacing=3,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                ],
                spacing=4,
            ),
        )

    def show_community_board_page(board_type="자유", selected_tab=None):
        clear_transient_ui()
        close_overlays()
        if board_type in {"자유게시판", "공유"}:
            board_type = "자유"
        if board_type not in {"인기", "자유", "리뷰", "질문"}:
            board_type = "자유"
        app_state["community_board_type"] = board_type
        # 리뷰·질문·자유게시판은 진입 경로와 관계없이 커뮤니티 탭에 속합니다.
        app_state["selected_tab"] = 0
        app_state["current_page"] = "community_board"

        board_labels = [
            ("인기글", "인기"),
            ("자유게시판", "자유"),
            ("리뷰", "리뷰"),
            ("질문", "질문"),
        ]
        category_labels = ["전체", "헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
        sort_labels = [("추천순", "popular"), ("최신순", "latest"), ("댓글순", "comment")]

        def choose_board(label):
            def handler(e):
                app_state["community_board_type"] = label
                show_community_board_page(label, app_state.get("selected_tab", 2))
            return handler

        def choose_category(label):
            def handler(e):
                app_state["community_category_filter"] = label
                app_state["community_filter_drawer"] = None
                show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 2))
            return handler

        def choose_sort(key):
            def handler(e):
                app_state["community_sort_mode"] = key
                app_state["community_filter_drawer"] = None
                show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 2))
            return handler

        def toggle_filter_drawer(kind):
            def handler(e):
                current = app_state.get("community_filter_drawer")
                app_state["community_filter_drawer"] = None if current == kind else kind
                show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 2))
            return handler

        def write_current(e=None):
            current = app_state.get("community_board_type", "질문")
            if current == "리뷰":
                app_state["review_target"] = None
                app_state["current_page"] = "write_review"
                show_write_review_page()
                return
            if current == "인기":
                current = "자유"
            if current == "전체":
                current = "질문"
            if current in {"스냅", "비디오"}:
                current = "자유"
            app_state["community_write_type"] = current
            show_write_community_page()

        current_board = app_state.get("community_board_type", "자유")
        current_category = app_state.get("community_category_filter", "전체")
        posts = filtered_community_posts(current_board, current_category)
        title_map = {
            "인기": ("인기글", "좋아요, 댓글, 저장을 합산한 인기 글이에요."),
            "리뷰": ("리뷰 게시판", "시술 경험과 가격, 만족도를 솔직하게 확인해요."),
            "질문": ("질문 게시판", "회원들과 먼저 묻고 답변을 나눠요."),
            "자유": ("자유게시판", "뷰티 수다와 고민을 가볍게 나눠요."),
        }
        title, subtitle = title_map.get(current_board, title_map["자유"])

        def board_tab(label, value):
            active = current_board == value
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=9),
                bgcolor=MAIN_COLOR if active else CHIP_BG,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else ft.Colors.with_opacity(0.0, BORDER_COLOR)),
                on_click=choose_board(value),
                ink=True,
                content=ft.Text(label, size=12, color="#FFFFFF" if active else SUBTEXT_COLOR, weight=ft.FontWeight.W_900 if active else ft.FontWeight.W_700),
            )

        def filter_chip(label, active, on_click, compact=False):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=12 if compact else 13, vertical=8),
                bgcolor=MAIN_COLOR if active else CARD_COLOR,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=on_click,
                ink=True,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                content=ft.Text(
                    label,
                    size=11,
                    color="#FFFFFF" if active else SUBTEXT_COLOR,
                    weight=ft.FontWeight.W_900 if active else ft.FontWeight.W_700,
                ),
            )

        def category_filter_chip(label):
            active = current_category == label
            return filter_chip(label, active, choose_category(label), compact=True)

        def sort_filter_chip(label, key):
            active = app_state.get("community_sort_mode", "popular") == key
            return filter_chip(label, active, choose_sort(key), compact=True)

        def drawer_button(label, value, kind):
            opened = app_state.get("community_filter_drawer") == kind
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                bgcolor=CHIP_BG if opened else CARD_COLOR,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if opened else BORDER_COLOR),
                on_click=toggle_filter_drawer(kind),
                ink=True,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                content=ft.Row(
                    controls=[
                        ft.Text(label, size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Text(value, size=11, color=MAIN_COLOR_DARK if opened else TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ft.Icon(app_icon("KEYBOARD_ARROW_UP" if opened else "KEYBOARD_ARROW_DOWN", "EXPAND_MORE"), size=15, color=MAIN_COLOR_DARK if opened else SUBTEXT_COLOR),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
            )

        def filter_drawer_panel():
            drawer = app_state.get("community_filter_drawer")
            if drawer == "category":
                controls = [category_filter_chip(label) for label in category_labels]
            elif drawer == "sort":
                controls = [sort_filter_chip(label, key) for label, key in sort_labels]
            else:
                return None
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=ft.Colors.with_opacity(0.58, CHIP_BG),
                border_radius=22,
                border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                content=ft.Row(
                    controls=controls,
                    spacing=7,
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def header_icon(icon_names, on_click, tooltip):
            return ft.Container(
                width=38,
                height=38,
                border_radius=19,
                alignment=ft.Alignment(0, 0),
                on_click=on_click,
                ink=True,
                tooltip=tooltip,
                content=ft.Icon(app_icon(*icon_names), size=24, color=TEXT_COLOR),
            )

        def sort_button():
            sort_order = ["popular", "latest", "comment"]
            label_map = {"popular": "추천순", "latest": "최신순", "comment": "댓글순"}
            current = app_state.get("community_sort_mode", "popular")

            def cycle_sort(e=None):
                next_index = (sort_order.index(current) + 1) % len(sort_order) if current in sort_order else 0
                app_state["community_sort_mode"] = sort_order[next_index]
                show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 0))

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=8),
                on_click=cycle_sort,
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Text(label_map.get(current, "추천순"), size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Icon(app_icon("SWAP_VERT", "UNFOLD_MORE"), size=14, color=SUBTEXT_COLOR),
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def write_floating_button():
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=13, vertical=7),
                bgcolor=MAIN_COLOR,
                border_radius=999,
                shadow=ft.BoxShadow(blur_radius=9, color="#18000000", offset=ft.Offset(0, 3)),
                on_click=write_current,
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon("ADD", "ADD_CIRCLE_OUTLINE"), size=15, color="#FFFFFF"),
                        ft.Text("글쓰기", size=12, color="#FFFFFF", weight=ft.FontWeight.W_900),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                    tight=True,
                ),
            )

        sort_label_map = {key: label for label, key in sort_labels}
        drawer_panel = filter_drawer_panel()

        cards = [
            ft.Container(
                width=content_width(),
                content=ft.Row(
                    controls=[board_tab(label, value) for label, value in board_labels],
                    spacing=8,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            ),
            ft.Container(
                width=content_width(),
                content=ft.Row(
                    controls=[
                        drawer_button("분야", current_category, "category"),
                        drawer_button("정렬", sort_label_map.get(app_state.get("community_sort_mode", "popular"), "추천순"), "sort"),
                        ft.Container(expand=True),
                        write_floating_button(),
                    ],
                    spacing=7,
                    scroll=ft.ScrollMode.HIDDEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            *([drawer_panel] if drawer_panel else []),
        ]
        if posts:
            cards.extend([community_result_card(item, back_page="community_board") for item in posts])
        else:
            cards.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor=CARD_COLOR,
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("아직 게시글이 없어요.", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                            ft.Text("첫 질문이나 리뷰를 남겨 커뮤니티를 시작해보세요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        cards.append(ft.Container(height=24))
        make_shell(ft.Column(controls=cards, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER), app_state["selected_tab"])

    def normalize_content_filter(category):
        if not category or category == "전체":
            return "전체"
        return normalize_overlay_category_name(category)

    def open_content_category(content_type, category_filter="전체", selected_tab=None):
        normalized_filter = normalize_content_filter(category_filter)
        app_state["left_menu_expanded"] = None
        close_overlays()

        if content_type == "리뷰":
            app_state["community_category_filter"] = normalized_filter
            show_community_board_page("리뷰", selected_tab=0 if selected_tab is None else selected_tab)
            return

        if content_type == "자유게시판":
            app_state["community_category_filter"] = normalized_filter
            show_community_board_page("자유", selected_tab=2 if selected_tab is None else selected_tab)
            return

        if content_type == "커뮤니티":
            app_state["community_category_filter"] = normalized_filter
            show_community_board_page("자유", selected_tab=2 if selected_tab is None else selected_tab)
            return

        if content_type == "스냅":
            app_state["snap_filter"] = normalized_filter
            app_state["selected_tab"] = 1 if selected_tab is None else selected_tab
            show_snap_page()
            return

        if content_type == "비디오":
            app_state["video_category_filter"] = normalized_filter
            app_state["active_video_index"] = 0
            app_state["selected_tab"] = 3 if selected_tab is None else selected_tab
            show_video_page()
            return

        show_community_board_page("자유", selected_tab=2 if selected_tab is None else selected_tab)

    def show_beauty_category_page(category_name="헤어"):
        clear_transient_ui()
        close_overlays()
        display_category = "반영구" if category_name == "반영구시술" else category_name
        app_state["selected_category"] = category_name
        app_state["selected_beauty_category"] = category_name
        app_state["selected_tab"] = 2
        app_state["current_page"] = "beauty_category_page"

        category_meta = {
            "헤어": {
                "icon": "CUT",
                "subtitle": "컷, 펌, 컬러, 드라이 팁을 헤어만 모아서 봐요.",
                "tips": ["앞머리", "레이어드컷", "볼륨", "컬러"],
            },
            "네일아트": {
                "icon": "BRUSH",
                "subtitle": "네일 디자인, 유지력, 손끝 관리 팁을 모았어요.",
                "tips": ["프렌치", "파츠", "유지력", "큐티클"],
            },
            "메이크업": {
                "icon": "FACE",
                "subtitle": "베이스, 립, 블러셔 조합과 데일리 팁을 모았어요.",
                "tips": ["베이스", "립조합", "블러셔", "톤"],
            },
            "반영구시술": {
                "icon": "AUTO_FIX_HIGH",
                "subtitle": "눈썹, 입술, 아이라인 관리와 회복 팁을 모았어요.",
                "tips": ["눈썹", "리터치", "탈각", "가격"],
            },
            "웨딩": {
                "icon": "FAVORITE",
                "subtitle": "본식, 하객, 촬영 전 준비 팁을 모았어요.",
                "tips": ["본식", "하객", "리허설", "고정"],
            },
            "포토": {
                "icon": "CAMERA_ALT",
                "subtitle": "프로필, 스냅, 셀프 촬영 팁을 모았어요.",
                "tips": ["프로필", "자연광", "포즈", "보정"],
            },
        }
        meta = category_meta.get(category_name, category_meta["헤어"])

        def open_board(board_type):
            def handler(e):
                app_state["community_category_filter"] = display_category
                show_community_board_page(board_type, selected_tab=2)
            return handler

        def open_snaps(e=None):
            app_state["snap_filter"] = display_category
            show_snap_page()

        def open_videos(e=None):
            app_state["video_category_filter"] = display_category
            show_video_page()

        category_labels = ["헤어", "네일아트", "메이크업", "포토", "웨딩", "반영구시술"]
        content_labels = [
            ("전체", "전체"),
            ("리뷰", "리뷰"),
            ("질문", "질문"),
            ("자유게시판", "자유"),
            ("스냅", "스냅"),
            ("비디오", "비디오"),
        ]
        current_content = app_state.get("beauty_category_content_filter", "전체")
        if current_content not in {value for _, value in content_labels}:
            current_content = "전체"
            app_state["beauty_category_content_filter"] = current_content

        def choose_beauty_category(label):
            def handler(e):
                app_state["beauty_category_content_filter"] = "전체"
                app_state["beauty_category_filter_drawer"] = None
                show_beauty_category_page(label)
            return handler

        def choose_content(value):
            def handler(e):
                app_state["beauty_category_content_filter"] = value
                app_state["beauty_category_filter_drawer"] = None
                show_beauty_category_page(category_name)
            return handler

        def toggle_beauty_drawer(kind):
            def handler(e):
                current = app_state.get("beauty_category_filter_drawer")
                app_state["beauty_category_filter_drawer"] = None if current == kind else kind
                show_beauty_category_page(category_name)
            return handler

        def drawer_option_chip(label, active, on_click):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=13, vertical=8),
                bgcolor=MAIN_COLOR if active else CARD_COLOR,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=on_click,
                ink=True,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_900 if active else ft.FontWeight.W_700,
                    text_align=ft.TextAlign.CENTER,
                ),
            )

        def beauty_drawer_button(label, value, kind):
            opened = app_state.get("beauty_category_filter_drawer") == kind
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=13, vertical=9),
                bgcolor=CHIP_BG if opened else CARD_COLOR,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if opened else BORDER_COLOR),
                on_click=toggle_beauty_drawer(kind),
                ink=True,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                content=ft.Row(
                    controls=[
                        ft.Text(label, size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Text(value, size=12, color=MAIN_COLOR_DARK if opened else TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ft.Icon(app_icon("KEYBOARD_ARROW_UP" if opened else "KEYBOARD_ARROW_DOWN", "EXPAND_MORE"), size=17, color=MAIN_COLOR_DARK if opened else SUBTEXT_COLOR),
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
            )

        def beauty_drawer_panel():
            drawer = app_state.get("beauty_category_filter_drawer")
            if drawer == "category":
                controls = [
                    drawer_option_chip(
                        "반영구" if label == "반영구시술" else label,
                        label == category_name,
                        choose_beauty_category(label),
                    )
                    for label in category_labels
                ]
            elif drawer == "content":
                controls = [
                    drawer_option_chip(label, current_content == value, choose_content(value))
                    for label, value in content_labels
                ]
            else:
                return None
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=ft.Colors.with_opacity(0.58, CHIP_BG),
                border_radius=22,
                border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                content=ft.Row(
                    controls=controls,
                    spacing=7,
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        category_posts = filtered_community_posts("전체", display_category)[:3]
        category_snaps = get_snap_feed_items("popular", display_category)[:4]
        category_videos = [video for video in get_all_video_items() if video.get("category") == display_category][:2]

        overview_card = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=18, vertical=18),
            bgcolor="#FFFFFF",
            border_radius=26,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=50,
                                height=50,
                                border_radius=18,
                                bgcolor=MAIN_COLOR_SOFT,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon(meta["icon"]), size=25, color=MAIN_COLOR),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(f"{display_category} 전용", size=20, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                                    ft.Text(meta["subtitle"], size=12, color=SUBTEXT_COLOR, max_lines=2),
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
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=11, vertical=7),
                                bgcolor=CHIP_BG,
                                border_radius=999,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.6, BORDER_COLOR)),
                                content=ft.Text(label, size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                            )
                            for label in meta["tips"]
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.HIDDEN,
                    ),
                ],
                spacing=14,
            ),
        )

        snap_cards = [
            ft.Container(
                width=96,
                on_click=open_snaps,
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=96,
                            height=116,
                            border_radius=16,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=black_image_box(96, 116),
                        ),
                        ft.Text(item.get("title", "스냅"), size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_700, max_lines=1),
                    ],
                    spacing=6,
                ),
            )
            for item in category_snaps
        ]

        def empty_card(message):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=16, vertical=22),
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Text(message, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
            )

        def community_cards_for(board_type, title_text, subtitle_text):
            posts = filtered_community_posts(board_type, display_category)[:4]
            return [
                section_title(title_text, subtitle_text, on_click=open_board(board_type)),
                *([community_result_card(post, back_page="beauty_category_page") for post in posts] or [
                    empty_card(f"아직 {display_category} {title_text}이 없어요.")
                ]),
            ]

        def snap_section():
            return [
                section_title(f"{display_category} 스냅", "사진으로 빠르게 분위기를 확인해요.", on_click=open_snaps),
                ft.Container(
                    width=content_width(),
                    height=146,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Row(controls=snap_cards, spacing=8, scroll=ft.ScrollMode.HIDDEN),
                ) if snap_cards else empty_card(f"아직 {display_category} 스냅이 없어요."),
            ]

        def video_section():
            return [
                section_title(f"{display_category} 비디오", "회원들이 올린 짧은 팁 영상이에요.", on_click=open_videos),
                *([message_video_tip_card(video) for video in category_videos] or [
                    empty_card(f"아직 {display_category} 비디오 팁이 없어요.")
                ]),
            ]

        content_sections = []
        if current_content == "전체":
            content_sections.extend(community_cards_for("전체", f"{display_category} 인기글", "리뷰, 질문, 공유글을 먼저 보여드려요."))
            content_sections.extend(snap_section())
            content_sections.extend(video_section())
        elif current_content in {"리뷰", "질문", "자유"}:
            title_label = "자유게시판" if current_content == "자유" else current_content
            content_sections.extend(
                community_cards_for(
                    current_content,
                    f"{display_category} {title_label}",
                    f"{display_category} 분야의 {title_label} 글만 모아봐요.",
                )
            )
        elif current_content == "스냅":
            content_sections.extend(snap_section())
        elif current_content == "비디오":
            content_sections.extend(video_section())

        content_label_map = {value: label for label, value in content_labels}
        selector_row = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[
                    beauty_drawer_button("분야", display_category, "category"),
                    beauty_drawer_button("보기", content_label_map.get(current_content, "전체"), "content"),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        drawer_panel = beauty_drawer_panel()

        body = ft.Column(
            controls=[
                brand_title_header(display_category),
                ft.Text(
                    "보고 싶은 분야와 글 종류를 골라 카테고리 안에서 바로 둘러봐요.",
                    width=content_width(),
                    size=12,
                    color=SUBTEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
                selector_row,
                *([drawer_panel] if drawer_panel else []),
                overview_card,
                *content_sections,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def open_category_recommendations(main_category, sub_category):
        if main_category in content_category_keys:
            open_content_category(main_category, sub_category)
            return

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
            on_click=lambda e: show_profile_page(),
            ink=True,
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

    def review_feed_items(include_non_visible=False):
        written = []
        for review in app_state.get("written_reviews", []):
            if review.get("status") == "deleted":
                continue
            if include_non_visible or review_visible_in_feed(review):
                written.append(review)

        defaults = []
        for idx, (name, category, body) in enumerate(REVIEW_ITEMS, start=1):
            defaults.append(
                {
                    "id": f"default_review_{idx}",
                    "shopName": "FINDY 커뮤니티 샵",
                    "artistName": name,
                    "artist_name": name,
                    "rating": 5,
                    "serviceCategory": normalize_overlay_category_name(category),
                    "category": category,
                    "reviewText": body,
                    "content": body,
                    "created_at": "추천 리뷰",
                    "createdAt": "추천 리뷰",
                    "verifiedVisit": True,
                    "status": "visible",
                    "images": [],
                    "photos": [],
                    "revisitIntent": "maybe",
                    "riskScore": 0,
                    "detectedRiskTypes": [],
                }
            )
        return list(reversed(written)) + defaults

    def show_review_report_dialog(review):
        review_id = review_identity(review)
        selected_reason = [REVIEW_REPORT_REASONS[0]]
        detail_field = ft.TextField(
            width=content_width() - 72,
            hint_text="신고 상세 내용을 입력해주세요.",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            border_radius=RADIUS_MD,
        )
        reason_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)

        def refresh_reason_row():
            reason_row.controls = [
                community_chip(
                    reason,
                    selected_reason[0] == reason,
                    lambda e, value=reason: (
                        selected_reason.__setitem__(0, value),
                        refresh_reason_row(),
                        page.update(),
                    ),
                )
                for reason in REVIEW_REPORT_REASONS
            ]

        def close_dialog(e=None):
            page.dialog.open = False
            page.update()

        def submit_report(e=None):
            reportReview(review_id, selected_reason[0], detail_field.value or "")
            close_dialog()
            show_snack("리뷰 신고가 접수되었어요. 운영팀이 확인할게요.")
            show_review_page()

        refresh_reason_row()
        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("리뷰 신고", size=18, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
            content=ft.Column(
                width=content_width() - 56,
                tight=True,
                controls=[
                    ft.Text("신고 사유", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                    reason_row,
                    detail_field,
                ],
                spacing=12,
            ),
            actions=[
                ft.TextButton("취소", on_click=close_dialog),
                ft.TextButton("신고", on_click=submit_report),
            ],
        )
        page.dialog.open = True
        page.update()

    def review_display_card(review, show_admin_meta=False):
        review_id = review_identity(review)
        rating = int(review.get("rating", 5) or 5)
        photos = review.get("images") or review.get("photos") or []
        verified = bool(review.get("verifiedVisit"))
        report_count = review_report_count(review_id)
        status = review.get("status", "visible")
        body_text = review.get("reviewText") or review.get("content") or ""
        positive = review.get("positiveComment", "")
        negative = review.get("negativeComment", "")
        review_text_parts = []
        if positive:
            review_text_parts.append(f"좋았던 점: {positive}")
        if negative:
            review_text_parts.append(f"아쉬웠던 점: {negative}")
        review_text_parts.append(body_text)

        if not show_admin_meta:
            review_item = {
                "type": "review",
                "id": review_id,
                "title": shop_display_name(review),
                "subtitle": f'{public_profile_name(review)} · {review.get("created_at", review.get("createdAt", ""))}',
                "description": " ".join([part for part in review_text_parts if part]),
                "badge": "리뷰",
                "category": service_category_label(review.get("serviceCategory") or review.get("category")),
                "meta": f"좋아요 {max(1, rating * 7)} · 댓글 {max(1, report_count)} · 조회 {max(80, rating * 143)}",
                "photos": photos,
                "source": review,
                "source_type": "review",
                "verifiedVisit": verified,
                "rating": rating,
            }

            def open_review_detail(e=None):
                app_state["content_detail_back_page"] = "review"
                open_content_detail(review_item, back_page="review")

            author, area, time_text = community_author_meta(review_item)
            metric_left, metric_right = compact_metric_text(review_item)
            stars = "★" * rating + "☆" * (5 - rating)
            verified_label = "인증된 방문 리뷰" if verified else "비인증 리뷰"
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=2, vertical=14),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                on_click=open_review_detail,
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                community_mini_badge("리뷰"),
                                community_mini_badge(review_item["category"]),
                                community_mini_badge(verified_label),
                                ft.Container(expand=True),
                                ft.Icon(app_icon("MORE_VERT", "MORE_HORIZ"), size=18, color=SUBTEXT_COLOR),
                            ],
                            spacing=6,
                        ),
                        ft.Text(review_item["title"], size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_900, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(review_item["description"], size=13, color=SUBTEXT_COLOR, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, height=1.35),
                        ft.Row(
                            controls=[
                                ft.Text(stars, size=11, color=MAIN_COLOR, weight=ft.FontWeight.W_900),
                                ft.Text(f"{author} · {area} · {time_text} · {metric_left}", size=10, color=SUBTEXT_COLOR, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                *[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(app_icon(icon), size=12, color=ft.Colors.with_opacity(0.45, SUBTEXT_COLOR)),
                                            ft.Text(value, size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                        ],
                                        spacing=2,
                                    )
                                    for icon, value in metric_right
                                ],
                            ],
                            spacing=5,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=6,
                ),
            )

        controls = [
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(review.get("shopName", "방문 정보 없음"), size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                            ft.Text(
                                f'{review.get("artistName", review.get("artist_name", "공개 표시명"))} · {review.get("created_at", review.get("createdAt", ""))}',
                                size=11,
                                color=SUBTEXT_COLOR,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    review_status_chip(status),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STAR_ROUNDED, size=14, color=MAIN_COLOR if i < rating else BORDER_COLOR)
                            for i in range(5)
                        ],
                        spacing=1,
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=9, vertical=4),
                        bgcolor=MAIN_COLOR_SOFT if verified else CHIP_BG,
                        border_radius=999,
                        content=ft.Text("인증된 방문 리뷰" if verified else "비인증 리뷰", size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(
                f'{service_category_label(review.get("serviceCategory"))} · 재방문 {revisit_intent_label(review.get("revisitIntent"))}',
                size=11,
                color=SUBTEXT_COLOR,
            ),
            ft.Text("\n".join([part for part in review_text_parts if part]), size=13, color=TEXT_COLOR, height=1.55),
        ]
        if photos:
            controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=68,
                            height=68,
                            border_radius=8,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=ft.Image(src=photo, width=68, height=68, fit=ft.ImageFit.COVER),
                        )
                        for photo in photos[:10]
                    ],
                    spacing=6,
                    scroll=ft.ScrollMode.HIDDEN,
                )
            )
        if show_admin_meta:
            controls.append(
                ft.Text(
                    f"신고 {report_count}회 · 위험도 {review.get('riskScore', 0)} · {', '.join(review.get('detectedRiskTypes', [])) or '감지 없음'}",
                    size=11,
                    color=SUBTEXT_COLOR,
                )
            )
        controls.append(
            ft.Container(
                width=content_width() - 36,
                content=ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            bgcolor="#FFFFFF",
                            border_radius=999,
                            border=ft.border.all(1, BORDER_COLOR),
                            ink=True,
                            on_click=lambda e: show_review_report_dialog(review),
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.FLAG_OUTLINED, size=15, color=SUBTEXT_COLOR),
                                    ft.Text("신고", size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                ],
                                spacing=5,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(controls=controls, spacing=9),
        )

    def show_review_page():
        app_state["community_board_type"] = "리뷰"
        app_state["selected_tab"] = 0
        show_community_board_page("리뷰", selected_tab=0)

    def show_write_review_page():
        app_state["current_page"] = "write_review"
        app_state["selected_tab"] = 4
        item = app_state.get("review_target")

        selected_rating = [0]
        selected_photos = []
        selected_service = [app_state.get("review_form_serviceCategory", "hair")]
        selected_revisit = [app_state.get("review_form_revisitIntent", "maybe")]
        review_policy_agreed = [False]
        legal_confirmed = [False]
        selectable_items = []
        seen_reservation_ids = set()
        candidates = ([item] if item else []) + list(reversed(app_state.get("reservation_history", [])))
        for candidate in candidates:
            if not candidate:
                continue
            reservation_id = candidate.get("id")
            if reservation_id in seen_reservation_ids:
                continue
            if classify_history_item(candidate) == "past" or candidate.get("status") == "시술 완료" or candidate == item:
                selectable_items.append(candidate)
                seen_reservation_ids.add(reservation_id)
        manual_target = {
            "id": "manual_review_target",
            "shopId": "manual_shop",
            "shopName": "",
            "artist_id": "manual_profile",
            "artist_name": "",
            "category": "헤어",
            "service": "직접 입력",
            "date": "",
            "status": "비인증",
        }
        selectable_items.append(manual_target)
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

        shop_name_field = ft.TextField(
            width=content_width(),
            hint_text="방문 장소 또는 서비스명",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        profile_name_field = ft.TextField(
            width=content_width(),
            hint_text="함께 표시할 공개명 또는 닉네임 (본명/연락처 입력 금지)",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        visit_purpose_field = ft.TextField(
            width=content_width(),
            hint_text="예: 커트 상담, 웨딩 촬영 준비, 네일 유지력 확인",
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        positive_field = ft.TextField(
            width=content_width(),
            hint_text="좋았던 점을 실제 경험 중심으로 적어주세요.",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        negative_field = ft.TextField(
            width=content_width(),
            hint_text="아쉬웠던 점은 비난보다 상황/경험 중심으로 적어주세요.",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=BORDER_COLOR,
            focused_border_color=MAIN_COLOR,
            bgcolor="#FAFAF8",
            border_radius=RADIUS_MD,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
        )
        content_field = ft.TextField(
            hint_text="전체 후기를 작성해주세요. 실명, 전화번호, 상세 주소, 인스타그램 ID, 카카오톡 ID는 입력하지 마세요.",
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
        risk_text = ft.Text("", size=12, color="#B85C5C")
        safe_examples = ft.Column(
            controls=[
                ft.Text("더 안전한 표현 예시", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                *[
                    ft.Text(f"• {item['safe']}", size=11, color=SUBTEXT_COLOR)
                    for item in SAFER_REVIEW_EXAMPLES
                ],
            ],
            spacing=4,
            visible=False,
        )
        submit_button = ft.Container(
            width=content_width(),
            height=52,
            border_radius=999,
            bgcolor=MAIN_COLOR,
            alignment=ft.Alignment(0, 0),
            ink=True,
            content=ft.Text("리뷰 등록", size=15, color="#FFFFFF", weight=ft.FontWeight.W_800),
        )

        selected_artist_text = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
        selected_meta_text = ft.Text("", size=12, color=SUBTEXT_COLOR)
        artist_option_controls = []

        def refresh_artist_selection():
            current = selected_item[0]
            verified = current.get("id") != "manual_review_target"
            selected_artist_text.value = public_profile_name(current) if verified else "직접 입력"
            selected_meta_text.value = (
                f'{shop_display_name(current)} · {current.get("service", current.get("category", ""))} · 인증된 방문'
                if verified
                else "예약 기록 없이 비인증 리뷰로 작성"
            )
            shop_name_field.value = "" if not verified else shop_display_name(current)
            profile_name_field.value = "" if not verified else public_profile_name(current)
            category = normalize_overlay_category_name(current.get("category", "헤어"))
            category_to_service = {
                "헤어": "hair",
                "네일아트": "nail",
                "메이크업": "makeup",
                "반영구": "tattoo",
                "포토": "photo",
                "웨딩": "wedding",
            }
            if not app_state.get("review_form_serviceCategory"):
                selected_service[0] = category_to_service.get(category, selected_service[0])
                app_state["review_form_serviceCategory"] = selected_service[0]
            for control, option in artist_option_controls:
                active = option.get("id") == current.get("id")
                control.bgcolor = MAIN_COLOR if active else "#FFFFFF"
                control.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
                control.content.controls[0].color = "#FFFFFF" if active else TEXT_COLOR
                control.content.controls[1].color = "#FFFFFF" if active else SUBTEXT_COLOR

        def select_artist(option):
            def handler(e):
                selected_item[0] = option
                app_state.pop("review_form_serviceCategory", None)
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
                        ft.Text(public_profile_name(option) if option.get("id") != "manual_review_target" else "직접 입력", size=12, weight=ft.FontWeight.W_600, max_lines=1),
                        ft.Text(option.get("service", option.get("category", "")), size=10, max_lines=1),
                    ],
                    spacing=3,
                ),
            )
            artist_option_controls.append((option_card, option))
            artist_option_row.controls.append(option_card)

        refresh_artist_selection()

        def refresh_risk_preview(e=None):
            combined = "\n".join(
                [
                    shop_name_field.value or "",
                    profile_name_field.value or "",
                    visit_purpose_field.value or "",
                    positive_field.value or "",
                    negative_field.value or "",
                    content_field.value or "",
                ]
            )
            risks = detectReviewRisks(combined)
            if risks:
                risk_text.value = f"{RISK_WARNING_MESSAGE} 감지 유형: {', '.join(risks)}"
                safe_examples.visible = True
            else:
                risk_text.value = ""
                safe_examples.visible = False
            can_submit_visual = review_policy_agreed[0] and legal_confirmed[0]
            submit_button.opacity = 1.0 if can_submit_visual else 0.45
            submit_button.bgcolor = MAIN_COLOR if can_submit_visual else BORDER_COLOR
            try:
                page.update()
            except Exception:
                pass

        def service_chip(label, key):
            return community_chip(
                label,
                selected_service[0] == key,
                lambda e, value=key: (
                    selected_service.__setitem__(0, value),
                    app_state.__setitem__("review_form_serviceCategory", value),
                    show_write_review_page(),
                ),
            )

        def revisit_chip(label, key):
            return community_chip(
                label,
                selected_revisit[0] == key,
                lambda e, value=key: (
                    selected_revisit.__setitem__(0, value),
                    app_state.__setitem__("review_form_revisitIntent", value),
                    show_write_review_page(),
                ),
            )

        def update_policy(e):
            review_policy_agreed[0] = bool(e.control.value)
            refresh_risk_preview()

        def update_legal(e):
            legal_confirmed[0] = bool(e.control.value)
            refresh_risk_preview()

        for field in [shop_name_field, profile_name_field, visit_purpose_field, positive_field, negative_field, content_field]:
            field.on_change = refresh_risk_preview

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
                    try:
                        validate_image_file(f.path)
                    except MediaStorageError as error:
                        show_snack(str(error), bgcolor="#B85C5C")
                        continue
                    if f.path not in selected_photos:
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
            if not review_policy_agreed[0] or not legal_confirmed[0]:
                show_snack("리뷰 정책 동의와 법적 책임 확인이 필요해요.", bgcolor="#B85C5C")
                return
            text = (content_field.value or "").strip()
            if not text:
                show_snack("리뷰 내용을 입력해주세요.", bgcolor="#B85C5C")
                return
            if not (shop_name_field.value or "").strip():
                show_snack("방문 장소 또는 서비스명을 입력해주세요.", bgcolor="#B85C5C")
                return
            if not (profile_name_field.value or "").strip():
                show_snack("공개 표시명을 입력해주세요.", bgcolor="#B85C5C")
                return

            target_item = selected_item[0]
            verified_visit = target_item.get("id") != "manual_review_target"
            already_written = verified_visit and any(
                r.get("reservation_id") == target_item.get("id")
                for r in app_state.get("written_reviews", [])
            )
            if already_written:
                show_snack("이미 이 서비스 리뷰를 작성했어요.", bgcolor="#B85C5C")
                return

            review = {
                "id": f"review_{len(app_state.get('written_reviews', [])) + 1}_{int(datetime.now().timestamp())}",
                "reservation_id": target_item.get("id"),
                "shopId": target_item.get("shopId", target_item.get("shop_id", "manual_shop")),
                "shopName": (shop_name_field.value or "").strip(),
                "artist_id": target_item.get("artist_id"),
                "artistId": target_item.get("artist_id"),
                "artistName": (profile_name_field.value or "").strip(),
                "artist_name": (profile_name_field.value or "").strip(),
                "displayName": (profile_name_field.value or "").strip(),
                "job": target_item.get("job", ""),
                "category": service_category_label(selected_service[0]),
                "serviceCategory": selected_service[0],
                "service": target_item.get("service", target_item.get("category", "")),
                "rating": selected_rating[0],
                "visitPurpose": (visit_purpose_field.value or "").strip(),
                "positiveComment": (positive_field.value or "").strip(),
                "negativeComment": (negative_field.value or "").strip(),
                "reviewText": text,
                "content": text,
                "revisitIntent": selected_revisit[0],
                "verifiedVisit": verified_visit,
                "reviewPolicyAgreed": review_policy_agreed[0],
                "legalResponsibilityConfirmed": legal_confirmed[0],
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "photos": list(selected_photos),
                "images": list(selected_photos),
            }
            validation = validateReviewBeforeSubmit(review)
            if not validation["canSubmit"]:
                risk_text.value = validation["message"]
                safe_examples.visible = True
                page.update()
                show_snack(validation["message"], bgcolor="#B85C5C")
                return
            review["status"] = validation["status"]
            review["riskScore"] = validation["riskScore"]
            review["detectedRiskTypes"] = validation["detectedRiskTypes"]
            review["visitPurpose"] = maskPersonalInfo(review["visitPurpose"])
            review["positiveComment"] = maskPersonalInfo(review["positiveComment"])
            review["negativeComment"] = maskPersonalInfo(review["negativeComment"])
            review["reviewText"] = maskPersonalInfo(review["reviewText"])
            review["content"] = review["reviewText"]
            try:
                stored_images = store_images(
                    selected_photos,
                    FINDY2_MEDIA_DIR,
                    current_user_id(),
                    limit=10,
                )
            except MediaStorageError as error:
                show_snack(str(error), bgcolor="#B85C5C")
                return
            review["photos"] = [item["path"] for item in stored_images]
            review["images"] = list(review["photos"])
            review["imageMetadata"] = stored_images
            cleanup_file_picker()
            if not submitReview(review):
                for stored_image in stored_images:
                    remove_media_file(stored_image.get("path"), FINDY2_MEDIA_DIR)
                return
            app_state.pop("review_form_serviceCategory", None)
            app_state.pop("review_form_revisitIntent", None)
            app_state["review_target"] = None
            open_completion_feedback(
                "리뷰가 등록되었어요" if validation["status"] == "visible" else "리뷰가 검토 대기로 저장되었어요",
                "작성한 리뷰는 내 활동과 리뷰 목록에서 확인할 수 있어요.",
                "내 후기 보기",
                "my_reviews",
                selected_tab=4,
                icon_name="RATE_REVIEW",
            )

        def go_back(e):
            cleanup_file_picker()
            app_state["review_target"] = None
            open_reservation_entry()

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
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
                    content=ft.Text(REVIEW_POLICY_NOTICE, size=12, color=TEXT_COLOR, height=1.55),
                ),
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("리뷰 대상", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
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
                            ft.Container(height=12),
                            ft.Text("방문 장소/서비스", size=12, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            shop_name_field,
                            ft.Text("공개 표시명", size=12, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            profile_name_field,
                            ft.Text("본명, 전화번호, 주소, 인스타그램 ID, 카카오톡 ID는 입력하지 마세요.", size=11, color="#B85C5C"),
                        ],
                        spacing=8,
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
                            ft.Text("방문 정보", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            visit_purpose_field,
                            ft.Text("시술 분야", size=12, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                            ft.Row(
                                controls=[service_chip(label, key) for key, label in REVIEW_SERVICE_OPTIONS],
                                spacing=8,
                                scroll=ft.ScrollMode.HIDDEN,
                            ),
                        ],
                        spacing=8,
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
                            ft.Text("좋았던 점", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            positive_field,
                            ft.Container(height=12),
                            ft.Text("아쉬웠던 점", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            negative_field,
                            ft.Container(height=12),
                            ft.Text("전체 후기", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Container(height=8),
                            content_field,
                            risk_text,
                            safe_examples,
                            ft.Container(height=10),
                            ft.Text("재방문 의사", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                            ft.Row(
                                controls=[revisit_chip(label, key) for key, label in REVIEW_REVISIT_OPTIONS],
                                spacing=8,
                                scroll=ft.ScrollMode.HIDDEN,
                            ),
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
                ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Checkbox(
                                label="리뷰 정책 동의 (reviewPolicyAgreed)",
                                value=False,
                                active_color=MAIN_COLOR,
                                check_color="#FFFFFF",
                                on_change=update_policy,
                            ),
                            ft.Text(REVIEW_POLICY_NOTICE, size=11, color=SUBTEXT_COLOR, height=1.45),
                            ft.Checkbox(
                                label="법적 책임 확인 (legalResponsibilityConfirmed)",
                                value=False,
                                active_color=MAIN_COLOR,
                                check_color="#FFFFFF",
                                on_change=update_legal,
                            ),
                            ft.Text(LEGAL_RESPONSIBILITY_NOTICE, size=11, color=SUBTEXT_COLOR, height=1.45),
                        ],
                        spacing=4,
                    ),
                ),
                ft.Container(height=8),
                submit_button,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        submit_button.on_click = submit_review
        refresh_risk_preview()
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

    def show_future_reservation_page(e=None):
        show_placeholder_info_page(
            "예약 서비스 준비 중",
            "FINDY2에서는 커뮤니티, 리뷰, 스냅, 비디오 활동 데이터를 먼저 모읍니다. 예약 기능은 추후 FINDY 본서비스에서 추천 알고리즘과 함께 연결할 예정이에요.",
        )

    def open_reservation_entry(e=None):
        if FINDY2_RESERVATION_ENABLED:
            show_reservation_history_page()
        else:
            show_future_reservation_page()

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
        back_page = app_state.get("content_detail_back_page", "my_content")
        item_type = item.get("post_type") or item.get("badge") or item.get("source_type")
        is_community_content = item_type in {
            "리뷰",
            "질문",
            "자유",
            "자유게시판",
            "community",
            "review",
        }
        if back_page in {"community_board", "review"} or is_community_content:
            app_state["selected_tab"] = 0
        elif back_page in {"home", "beauty_category_page"}:
            app_state["selected_tab"] = 2
        else:
            app_state["selected_tab"] = 4

        def go_back(e=None):
            if back_page == "saved_content":
                show_saved_content_page()
            elif back_page == "search_results":
                show_search_results_page()
            elif back_page == "community_board":
                show_community_board_page(app_state.get("community_board_type", "자유"), app_state.get("selected_tab", 2))
            elif back_page == "review":
                show_review_page()
            elif back_page == "home":
                show_home_page()
            elif back_page == "beauty_category_page":
                show_beauty_category_page(app_state.get("selected_beauty_category", "헤어"))
            else:
                show_my_content_page()

        source = item.get("source") if isinstance(item.get("source"), dict) else item
        normalized_type = str(item_type or "").strip().lower()
        is_review_detail = normalized_type in {"리뷰", "review"} or item.get("source_type") == "review"
        is_question_detail = normalized_type in {"질문", "question"}
        photos = item.get("photos") or item.get("images") or source.get("photos") or source.get("images") or []
        content_id = content_identity(item)
        liked_ids = app_state.setdefault("community_liked_ids", set())
        saved_ids = app_state.setdefault("community_saved_ids", set())
        answered_question_ids = app_state.setdefault("answered_question_ids", set())
        content_reports = app_state.setdefault("content_reports", [])
        comment_store = app_state.setdefault("content_comments", {})
        comments = comment_store.setdefault(content_id, [])
        comment_liked_ids = app_state.setdefault("comment_liked_ids", set())
        base_likes = extract_metric(item.get("meta", ""), "좋아요")
        base_saves = extract_metric(item.get("meta", ""), "저장")
        base_comments = extract_metric(item.get("meta", ""), "댓글")
        comment_field = ft.TextField(
            width=content_width(),
            hint_text="댓글을 입력해주세요.",
            border=ft.InputBorder.NONE,
            focused_border_color=MAIN_COLOR,
            bgcolor=ft.Colors.TRANSPARENT,
            text_style=ft.TextStyle(size=12, color=TEXT_COLOR),
            hint_style=ft.TextStyle(size=12, color=SUBTEXT_COLOR),
            content_padding=ft.padding.symmetric(horizontal=10, vertical=7),
        )
        selected_comment_photos = []
        selected_comment_location = [""]
        reply_target = [None]

        def report_content(e=None):
            if item.get("source_type") == "review" and isinstance(item.get("source"), dict):
                show_review_report_dialog(item["source"])
                return

            selected_reason = ["허위 정보"]
            reason_options = ["허위 정보", "욕설/비방", "개인정보 노출", "사생활 침해", "광고/스팸", "기타"]
            reason_controls = ft.Row(spacing=6, wrap=True)
            detail_field = ft.TextField(
                hint_text="필요한 경우 상세 내용을 입력해주세요.",
                multiline=True,
                min_lines=2,
                max_lines=4,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                text_size=12,
            )

            def refresh_reasons():
                reason_controls.controls = [
                    community_mini_badge(
                        reason,
                        on_click=lambda event, value=reason: select_reason(value),
                        selected=selected_reason[0] == reason,
                    )
                    for reason in reason_options
                ]
                page.update()

            def select_reason(reason):
                selected_reason[0] = reason
                refresh_reasons()

            def close_report_dialog(event=None):
                page.dialog.open = False
                page.update()

            def submit_report(event=None):
                already_reported = any(
                    report.get("contentId") == content_id
                    and report.get("reporterUserId") == current_user_id()
                    and report.get("status") == "pending"
                    for report in content_reports
                )
                if already_reported:
                    close_report_dialog()
                    show_snack("이미 검토 중인 신고가 있어요.")
                    return
                content_reports.append(
                    {
                        "id": f"content_report_{len(content_reports) + 1}_{int(datetime.now().timestamp())}",
                        "contentId": content_id,
                        "reporterUserId": current_user_id(),
                        "reason": selected_reason[0],
                        "detail": (detail_field.value or "").strip(),
                        "status": "pending",
                        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                )
                app_state.setdefault("reported_content_ids", set()).add(content_id)
                persist_user_data()
                close_report_dialog()
                show_snack("신고가 접수되었어요. 운영팀이 확인할게요.")
                show_content_detail_page()

            refresh_reasons()
            page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("게시글 신고", size=17, weight=ft.FontWeight.W_900),
                content=ft.Container(
                    width=min(330, content_width() - 24),
                    content=ft.Column(
                        controls=[
                            ft.Text("신고 사유를 선택해주세요.", size=11, color=SUBTEXT_COLOR),
                            reason_controls,
                            detail_field,
                        ],
                        spacing=12,
                        tight=True,
                    ),
                ),
                actions=[
                    ft.TextButton("취소", on_click=close_report_dialog),
                    ft.TextButton("신고", on_click=submit_report),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.dialog.open = True
            page.update()

        def toggle_question_answered(e=None):
            if not is_owned_by_current_user(source):
                show_snack("질문 작성자만 답변 상태를 변경할 수 있어요.", bgcolor="#B85C5C")
                return
            if content_id in answered_question_ids:
                answered_question_ids.discard(content_id)
                show_snack("답변 대기 상태로 변경했어요.")
            else:
                answered_question_ids.add(content_id)
                show_snack("답변 완료로 표시했어요.")
            persist_user_data()
            show_content_detail_page()

        def delete_owned_content(e=None):
            source = item.get("source") if isinstance(item.get("source"), dict) else item
            if not is_owned_by_current_user(source):
                show_snack("작성자 본인만 삭제할 수 있어요.", bgcolor="#B85C5C")
                return
            source_id = source.get("id")
            collection_keys = ("community_posts", "written_snaps", "written_videos", "written_reviews")
            deleted = False
            for key in collection_keys:
                collection = app_state.get(key, [])
                remaining = [
                    entry
                    for entry in collection
                    if entry is not source and (not source_id or entry.get("id") != source_id)
                ]
                if len(remaining) != len(collection):
                    app_state[key] = remaining
                    deleted = True
            if not deleted:
                show_snack("삭제할 글을 찾지 못했어요.", bgcolor="#B85C5C")
                return
            app_state.get("community_liked_ids", set()).discard(content_id)
            app_state.get("community_saved_ids", set()).discard(content_id)
            app_state.get("content_comments", {}).pop(content_id, None)
            if not persist_user_data(notify_on_error=True):
                show_snack("삭제 상태를 저장하지 못했어요.", bgcolor="#B85C5C")
                return
            media_paths = list(source.get("photos") or source.get("images") or [])
            video_path = source.get("video_path")
            if video_path:
                media_paths.append(video_path)
            for media_path in media_paths:
                remove_media_file(media_path, FINDY2_MEDIA_DIR)
            show_snack("내 글이 삭제되었어요.")
            go_back()

        def toggle_content_like(e=None):
            if content_id in liked_ids:
                liked_ids.discard(content_id)
                show_snack("좋아요를 취소했어요.")
            else:
                liked_ids.add(content_id)
                show_snack("좋아요를 눌렀어요.")
            persist_user_data()
            show_content_detail_page()

        def toggle_content_save(e=None):
            if content_id in saved_ids:
                saved_ids.discard(content_id)
                show_snack("저장을 취소했어요.")
            else:
                saved_ids.add(content_id)
                show_snack("저장했어요.")
            persist_user_data()
            show_content_detail_page()

        def submit_content_comment(e=None):
            text = (comment_field.value or "").strip()
            if not text and not selected_comment_photos and not selected_comment_location[0]:
                show_snack("댓글을 입력해주세요.", bgcolor="#B85C5C")
                return
            comments.append({
                "id": f"{content_id}:comment:{len(comments) + 1}",
                "userId": current_user_id(),
                "author": current_user_label(),
                "text": text,
                "time": "방금 전",
                "likes": 0,
                "replyTo": reply_target[0],
                "photos": list(selected_comment_photos),
                "location": selected_comment_location[0],
            })
            selected_comment_photos.clear()
            selected_comment_location[0] = ""
            reply_target[0] = None
            persist_user_data()
            show_snack("댓글이 등록되었어요.")
            show_content_detail_page()

        def on_comment_photo_picked(e: ft.FilePickerResultEvent):
            if not e.files or not e.files[0].path:
                return
            try:
                validate_image_file(e.files[0].path)
                stored = store_images(
                    [e.files[0].path],
                    FINDY2_MEDIA_DIR,
                    current_user_id(),
                    limit=1,
                )
                selected_comment_photos[:] = [stored[0]["path"]]
                show_snack("댓글에 사진 1장을 첨부했어요.")
            except MediaStorageError as error:
                show_snack(str(error), bgcolor="#B85C5C")

        comment_photo_picker = ft.FilePicker(on_result=on_comment_photo_picked)
        page.overlay.append(comment_photo_picker)

        def pick_comment_photo(e=None):
            comment_photo_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["jpg", "jpeg", "png", "webp", "heic"],
            )

        def add_comment_location(e=None):
            selected_comment_location[0] = "내 주변"
            show_snack("댓글에 위치 정보를 추가했어요.")

        def add_comment_emoji(emoji):
            def handler(e=None):
                comment_field.value = f"{comment_field.value or ''}{emoji}"
                page.dialog.open = False
                page.update()
            return handler

        def open_comment_emoji_picker(e=None):
            page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("이모지", size=16, weight=ft.FontWeight.W_900),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=12,
                            alignment=ft.Alignment(0, 0),
                            ink=True,
                            on_click=add_comment_emoji(emoji),
                            content=ft.Text(emoji, size=22),
                        )
                        for emoji in ["😊", "👍", "❤️", "✨", "궁금", "공감"]
                    ],
                    spacing=6,
                    wrap=True,
                ),
            )
            page.dialog.open = True
            page.update()

        def content_action_button(icon_name, label, value, active, on_click):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                bgcolor=MAIN_COLOR_SOFT if active else ft.Colors.TRANSPARENT,
                border_radius=12,
                on_click=on_click,
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=15, color=MAIN_COLOR if active else SUBTEXT_COLOR),
                        ft.Text(f"{label} {value}", size=10, color=MAIN_COLOR_DARK if active else SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
            )

        def detail_info_chip(label, icon_name=None, emphasized=False, on_click=None):
            controls = []
            if icon_name:
                controls.append(
                    ft.Icon(
                        app_icon(icon_name),
                        size=13,
                        color="#FFFFFF" if emphasized else MAIN_COLOR,
                    )
                )
            controls.append(
                ft.Text(
                    label,
                    size=9,
                    color="#FFFFFF" if emphasized else MAIN_COLOR_DARK,
                    weight=ft.FontWeight.W_800,
                )
            )
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=5),
                bgcolor=MAIN_COLOR if emphasized else ft.Colors.with_opacity(0.55, CHIP_BG),
                border=ft.border.all(1, MAIN_COLOR if emphasized else BORDER_COLOR),
                border_radius=999,
                on_click=on_click,
                ink=on_click is not None,
                content=ft.Row(controls=controls, spacing=4, tight=True),
            )

        author, area, time_text = community_author_meta(item)
        comment_field.height = 38
        comment_field.expand = True
        review_rating = max(
            0.0,
            min(5.0, float(item.get("rating", source.get("rating", 5)) or 5)),
        )
        review_category = service_category_label(
            item.get("category")
            or item.get("serviceCategory")
            or source.get("serviceCategory")
            or source.get("category")
        )
        verified_visit = bool(item.get("verifiedVisit", source.get("verifiedVisit", False)))
        question_answered = content_id in answered_question_ids
        content_reported = content_id in app_state.setdefault("reported_content_ids", set())
        display_comments = comments[-6:] if comments else [
            {"id": f"{content_id}:seed:1", "author": "FINDY 회원", "text": "저도 궁금했던 내용이에요.", "time": "첫 댓글", "likes": 0},
            {"id": f"{content_id}:seed:2", "author": "뷰티기록", "text": "경험 공유해줘서 고마워요.", "time": "방금 전", "likes": 0},
        ]

        def detail_icon_button(icon_name, on_click=None):
            return ft.Container(
                width=34,
                height=34,
                border_radius=17,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=on_click,
                content=ft.Icon(app_icon(icon_name), size=22, color=TEXT_COLOR),
            )

        def detail_avatar(label, size=32):
            initial = (label or "F")[0]
            return ft.Container(
                width=size,
                height=size,
                border_radius=size / 2,
                bgcolor=MAIN_COLOR_SOFT,
                alignment=ft.Alignment(0, 0),
                content=ft.Text(initial, size=12 if size <= 32 else 14, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_900),
            )

        def detail_comment_row(comment):
            comment_id = str(comment.get("id") or f"{content_id}:{comment.get('author')}:{comment.get('time')}")
            liked = comment_id in comment_liked_ids
            likes = int(comment.get("likes", 0) or 0) + (1 if liked else 0)

            def toggle_comment_like(e=None):
                if liked:
                    comment_liked_ids.discard(comment_id)
                else:
                    comment_liked_ids.add(comment_id)
                persist_user_data()
                show_content_detail_page()

            def reply_to_comment(e=None):
                reply_target[0] = comment.get("author", "FINDY 회원")
                comment_field.value = f"@{reply_target[0]} "
                comment_field.focus()
                page.update()

            def open_comment_menu(e=None):
                page.dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("댓글 메뉴", size=16, weight=ft.FontWeight.W_900),
                    content=ft.Column(
                        tight=True,
                        controls=[
                            ft.TextButton("댓글 신고", on_click=lambda event: (setattr(page.dialog, "open", False), show_snack("댓글 신고가 접수되었어요."), page.update())),
                            ft.TextButton("취소", on_click=lambda event: (setattr(page.dialog, "open", False), page.update())),
                        ],
                    ),
                )
                page.dialog.open = True
                page.update()

            comment_meta = " · ".join(
                value
                for value in [
                    comment.get("time", ""),
                    comment.get("location", ""),
                ]
                if value
            )
            comment_photos = comment.get("photos") or []
            comment_body_controls = []
            if comment.get("replyTo"):
                comment_body_controls.append(
                    ft.Text(
                        f"@{comment.get('replyTo')}",
                        size=9,
                        color=MAIN_COLOR,
                        weight=ft.FontWeight.W_800,
                    )
                )
            if comment.get("text"):
                comment_body_controls.append(
                    ft.Text(
                        comment.get("text", ""),
                        size=12,
                        color=TEXT_COLOR,
                    )
                )
            if comment_photos:
                comment_body_controls.append(
                    ft.Container(
                        width=76,
                        height=76,
                        border_radius=10,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Image(
                            src=comment_photos[0],
                            width=76,
                            height=76,
                            fit=ft.ImageFit.COVER,
                        ),
                    )
                )
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=7),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.35, BORDER_COLOR))),
                content=ft.Row(
                    controls=[
                        detail_avatar(comment.get("author", "F"), 30),
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(comment.get("author", "FINDY 회원"), size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                                        ft.Text(comment_meta, size=9, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=5,
                                ),
                                *comment_body_controls,
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            on_click=toggle_comment_like,
                                            ink=True,
                                            content=ft.Text(
                                                f"좋아요{f' {likes}' if likes else ''}",
                                                size=9,
                                                color=MAIN_COLOR if liked else SUBTEXT_COLOR,
                                                weight=ft.FontWeight.W_800,
                                            ),
                                        ),
                                        ft.Container(
                                            on_click=reply_to_comment,
                                            ink=True,
                                            content=ft.Text("답글", size=9, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ),
                                    ],
                                    spacing=10,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Container(
                            width=26,
                            height=26,
                            alignment=ft.Alignment(0, 0),
                            on_click=open_comment_menu,
                            ink=True,
                            content=ft.Icon(app_icon("MORE_VERT", "MORE_HORIZ"), size=15, color=SUBTEXT_COLOR),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            )

        detail_status_controls = []
        if is_review_detail:
            detail_status_controls.append(
                ft.Row(
                    controls=[
                        detail_info_chip(review_category or "리뷰"),
                        detail_info_chip(
                            "인증된 방문" if verified_visit else "비인증 리뷰",
                            "VERIFIED_OUTLINED" if verified_visit else None,
                            emphasized=verified_visit,
                        ),
                        ft.Container(expand=True),
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.STAR_ROUNDED
                                    if index < int(round(review_rating))
                                    else ft.Icons.STAR_BORDER_ROUNDED,
                                    size=15,
                                    color=MAIN_COLOR if index < int(round(review_rating)) else BORDER_COLOR,
                                )
                                for index in range(5)
                            ],
                            spacing=0,
                        ),
                        ft.Text(
                            f"{review_rating:.1f}",
                            size=10,
                            color=MAIN_COLOR_DARK,
                            weight=ft.FontWeight.W_900,
                        ),
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        elif is_question_detail:
            detail_status_controls.append(
                ft.Row(
                    controls=[
                        detail_info_chip(
                            "답변 완료" if question_answered else "답변 기다리는 중",
                            "CHECK_CIRCLE_OUTLINE" if question_answered else "SCHEDULE",
                            emphasized=question_answered,
                        ),
                        ft.Container(expand=True),
                        detail_info_chip(
                            "답변 대기로 변경" if question_answered else "답변 완료",
                            "CHECK",
                            on_click=toggle_question_answered,
                        )
                        if is_owned_by_current_user(source)
                        else ft.Container(),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        content_controls = [
            ft.Container(
                width=content_width(),
                height=40,
                content=ft.Row(
                    controls=[
                        detail_icon_button("ARROW_BACK_IOS_NEW", go_back),
                        ft.Container(expand=True),
                        detail_icon_button(
                            "SHARE_OUTLINED",
                            lambda e: show_snack("공유 링크가 준비되었어요."),
                        ),
                        detail_icon_button(
                            "DELETE_OUTLINE" if is_owned_by_current_user(item) else "MORE_VERT",
                            delete_owned_content if is_owned_by_current_user(item) else report_content,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            ft.Container(
                width=content_width(),
                padding=ft.padding.only(top=4, bottom=6),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                community_mini_badge(item.get("badge", "글")),
                                ft.Container(expand=True),
                                ft.Text(f"{area} · {time_text}", size=9, color=SUBTEXT_COLOR),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        *detail_status_controls,
                        ft.Text(
                            item.get("title", "제목 없음"),
                            size=21,
                            weight=ft.FontWeight.W_900,
                            color=TEXT_COLOR,
                        ),
                        ft.Text(
                            item.get("description", "내용이 없어요."),
                            size=14,
                            color=TEXT_COLOR,
                        ),
                        ft.Row(
                            controls=[
                                detail_avatar(author, 28),
                                ft.Text(author, size=10, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                                ft.Container(expand=True),
                                content_action_button(
                                    "FAVORITE" if content_id in liked_ids else "FAVORITE_BORDER",
                                    "좋아요",
                                    base_likes + (1 if content_id in liked_ids else 0),
                                    content_id in liked_ids,
                                    toggle_content_like,
                                ),
                                content_action_button(
                                    "BOOKMARK" if content_id in saved_ids else "BOOKMARK_BORDER",
                                    "저장",
                                    base_saves + (1 if content_id in saved_ids else 0),
                                    content_id in saved_ids,
                                    toggle_content_save,
                                ),
                            ],
                            spacing=5,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
            ),
        ]
        if photos:
            content_controls.append(
                ft.Row(
                    width=content_width(),
                    spacing=8,
                    scroll=ft.ScrollMode.HIDDEN,
                    controls=[
                        ft.Container(
                            width=content_width() if len(photos) == 1 else max(220, content_width() - 56),
                            height=230,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            border_radius=12,
                            content=ft.Image(
                                src=photo,
                                width=content_width() if len(photos) == 1 else max(220, content_width() - 56),
                                height=230,
                                fit=ft.ImageFit.COVER,
                            ),
                        )
                        for photo in photos[:6]
                    ],
                )
            )
        content_controls.append(
            ft.Container(
                width=content_width(),
                padding=ft.padding.only(top=4),
                content=ft.Column(
                    controls=[
                        ft.Container(height=1, bgcolor=BORDER_COLOR),
                        ft.Row(
                            controls=[
                                ft.Text("댓글", size=14, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
                                ft.Text(f"{base_comments + len(comments)}", size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                ft.Container(expand=True),
                                ft.Text("최신순", size=9, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        *[detail_comment_row(comment) for comment in display_comments],
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            bgcolor=ft.Colors.with_opacity(0.68, CHIP_BG),
                            border_radius=17,
                            border=ft.border.all(1, BORDER_COLOR),
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        width=28,
                                        height=28,
                                        alignment=ft.Alignment(0, 0),
                                        on_click=pick_comment_photo,
                                        ink=True,
                                        tooltip="사진 첨부",
                                        content=ft.Icon(app_icon("IMAGE_OUTLINED", "PHOTO_LIBRARY_OUTLINED"), size=18, color=SUBTEXT_COLOR),
                                    ),
                                    ft.Container(
                                        width=28,
                                        height=28,
                                        alignment=ft.Alignment(0, 0),
                                        on_click=add_comment_location,
                                        ink=True,
                                        tooltip="장소 추가",
                                        content=ft.Icon(app_icon("LOCATION_ON_OUTLINED", "PLACE_OUTLINED"), size=18, color=SUBTEXT_COLOR),
                                    ),
                                    comment_field,
                                    ft.Container(
                                        width=28,
                                        height=28,
                                        alignment=ft.Alignment(0, 0),
                                        on_click=open_comment_emoji_picker,
                                        ink=True,
                                        tooltip="이모지",
                                        content=ft.Icon(app_icon("SENTIMENT_SATISFIED_ALT_OUTLINED", "INSERT_EMOTICON"), size=18, color=SUBTEXT_COLOR),
                                    ),
                                    ft.Container(
                                        width=30,
                                        height=30,
                                        border_radius=15,
                                        alignment=ft.Alignment(0, 0),
                                        bgcolor=MAIN_COLOR,
                                        on_click=submit_content_comment,
                                        ink=True,
                                        tooltip="댓글 전송",
                                        content=ft.Icon(app_icon("SEND", "ARROW_FORWARD"), size=16, color="#FFFFFF"),
                                    ),
                                ],
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ),
                    ],
                    spacing=8,
                ),
            )
        )
        content_controls.append(
            ft.Container(
                width=content_width(),
                alignment=ft.Alignment(1, 0),
                content=ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=5),
                    border_radius=10,
                    on_click=report_content,
                    ink=True,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FLAG_OUTLINED, size=13, color=SUBTEXT_COLOR),
                            ft.Text(
                                "신고 검토 중" if content_reported else "신고",
                                size=9,
                                color=SUBTEXT_COLOR,
                                weight=ft.FontWeight.W_700,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
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
        content_type = app_state.get("my_content_type", "전체")
        app_state["current_page"] = "my_content"
        app_state["selected_tab"] = 4

        content_tabs = ["전체", "질문", "자유게시판", "스냅", "비디오"]
        if content_type not in content_tabs:
            content_type = "전체"
            app_state["my_content_type"] = content_type

        def snap_items():
            return [
                make_simple_content_item(
                    "snap",
                    item.get("title"),
                    f'{item.get("category", "스냅")} · 스냅',
                    item.get("description", ""),
                    "스냅",
                    f'좋아요 {item.get("likes", 0)} · 저장 {item.get("saves", 0)}',
                    item,
                )
                for item in app_state.get("written_snaps", [])
            ]

        def video_items():
            return [
                make_simple_content_item(
                    "video",
                    item.get("title"),
                    f'{item.get("category", "비디오")} · {item.get("duration", "0:00")}',
                    item.get("subtitle", ""),
                    "비디오",
                    f'조회 {item.get("views", "0")}',
                    item,
                )
                for item in app_state.get("written_videos", [])
            ]

        def community_items(post_type=None):
            posts = app_state.get("community_posts", [])
            if post_type:
                posts = [item for item in posts if item.get("post_type", item.get("badge")) == post_type]
            return [
                make_simple_content_item(
                    "community",
                    item.get("title", "커뮤니티 글"),
                    f'{item.get("category", "커뮤니티")} · {item.get("post_type", item.get("badge", "커뮤니티"))}',
                    item.get("description") or item.get("body", ""),
                    "커뮤니티",
                    item.get("meta", "댓글 0 · 저장 0"),
                    item,
                )
                for item in posts
            ]

        if content_type == "질문":
            items = community_items("질문")
        elif content_type == "자유게시판":
            items = community_items("자유")
        elif content_type == "스냅":
            items = snap_items()
        elif content_type == "비디오":
            items = video_items()
        else:
            items = community_items() + snap_items() + video_items()

        def content_tab(label):
            active = content_type == label
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=9),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=lambda e, selected=label: show_my_content_page(selected),
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_800,
                ),
            )

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
            page_header("내가 쓴글", on_back=go_back_page),
            ft.Text("질문, 자유게시판, 스냅, 비디오까지 앱 안에서 작성한 글을 모아봤어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
            ft.Row(
                controls=[content_tab(label) for label in content_tabs],
                spacing=8,
                run_spacing=8,
                wrap=True,
                width=content_width(),
            ),
        ]
        visible_items = [item for item in items if not is_content_hidden(item)]
        if visible_items:
            controls.extend([browse_result_card(item, on_click=open_item(item)) for item in visible_items])
        else:
            write_target = {
                "스냅": show_write_snap_page,
                "비디오": show_write_video_page,
                "질문": lambda: (app_state.__setitem__("community_write_type", "질문"), show_write_community_page()),
                "자유게시판": lambda: (app_state.__setitem__("community_write_type", "자유"), show_write_community_page()),
            }.get(content_type, show_write_community_page)
            empty_label = "글" if content_type == "전체" else content_type
            controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(f"아직 작성한 {empty_label}이 없어요.", size=15, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("첫 콘텐츠를 작성하면 이곳에서 바로 확인할 수 있어요.", size=12, color=SUBTEXT_COLOR),
                            soft_button(f"{empty_label} 작성하기", MAIN_COLOR, "white", lambda e: write_target(), width=content_width() - 48),
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
        content_type = app_state.get("saved_content_type", "전체")
        app_state["current_page"] = "saved_content"
        app_state["selected_tab"] = 4

        content_tabs = ["전체", "질문", "자유게시판", "스냅", "비디오"]
        if content_type not in content_tabs:
            content_type = "전체"
            app_state["saved_content_type"] = content_type

        def saved_snap_items():
            items = []
            saved_ids = app_state.get("snap_saved_ids", set())
            for category in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]:
                for snap in get_snap_feed_items("latest", category):
                    if snap.get("id") in saved_ids:
                        items.append(make_simple_content_item("snap", snap.get("title"), snap.get("category"), snap.get("description", ""), "스냅", f'좋아요 {snap.get("likes", 0)} · 저장 {snap.get("saves", 0)}', snap))
            return items

        def saved_video_items():
            items = []
            saved_keys = app_state.get("video_saved_keys", set())
            for video in get_all_video_items():
                if video_key(video) in saved_keys:
                    items.append(make_simple_content_item("video", video.get("title"), video.get("category"), video.get("subtitle", ""), "비디오", f'{video.get("duration", "0:00")} · 조회 {video.get("views", "0")}', video))
            return items

        def saved_community_items(post_type_filter=None):
            items = []
            saved_keys = app_state.get("community_saved_ids", set())
            for post in community_posts():
                post_type = post.get("post_type", post.get("badge", "커뮤니티"))
                if content_identity(post) in saved_keys and (post_type_filter is None or post_type == post_type_filter):
                    items.append(make_simple_content_item(
                        "community",
                        post.get("title", "커뮤니티 글"),
                        f'{post.get("category", "커뮤니티")} · {post_type}',
                        post.get("description", ""),
                        post_type,
                        post.get("meta", "댓글 0 · 저장 0"),
                        post,
                    ))
            return items

        if content_type in {"질문", "자유게시판"}:
            items = saved_community_items("자유" if content_type == "자유게시판" else content_type)
        elif content_type == "스냅":
            items = saved_snap_items()
        elif content_type == "비디오":
            items = saved_video_items()
        else:
            items = saved_community_items() + saved_snap_items() + saved_video_items()

        def content_tab(label):
            active = content_type == label
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=9),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=lambda e, selected=label: show_saved_content_page(selected),
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_800,
                ),
            )

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
            page_header("저장", on_back=go_back_page),
            ft.Text("저장한 커뮤니티 글, 스냅, 비디오를 모아봤어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
            ft.Row(
                controls=[content_tab(label) for label in content_tabs],
                spacing=8,
                run_spacing=8,
                wrap=True,
                width=content_width(),
            ),
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
                            ft.Text("아직 저장한 글이 없어요.", size=15, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("저장 버튼을 누르면 이곳에 모여요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        controls.append(ft.Container(height=24))
        make_shell(ft.Column(controls=controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER), app_state["selected_tab"])

    def show_liked_content_page(content_type="전체"):
        app_state["current_page"] = "liked_content"
        app_state["selected_tab"] = 4

        content_tabs = ["전체", "질문", "자유게시판", "스냅", "비디오"]
        if content_type not in content_tabs:
            content_type = "전체"

        def liked_snap_items():
            items = []
            liked_ids = app_state.get("snap_liked_ids", set())
            for category in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]:
                for snap in get_snap_feed_items("latest", category):
                    if snap.get("id") in liked_ids:
                        items.append(make_simple_content_item("snap", snap.get("title"), snap.get("category"), snap.get("description", ""), "스냅", f'좋아요 {snap.get("likes", 0)} · 저장 {snap.get("saves", 0)}', snap))
            return items

        def liked_video_items():
            items = []
            liked_keys = app_state.get("video_liked_keys", set())
            for video in get_all_video_items():
                if video_key(video) in liked_keys:
                    items.append(make_simple_content_item("video", video.get("title"), video.get("category"), video.get("subtitle", ""), "비디오", f'{video.get("duration", "0:00")} · 조회 {video.get("views", "0")}', video))
            return items

        def liked_community_items(post_type_filter=None):
            items = []
            liked_ids = app_state.get("community_liked_ids", set())
            for post in community_posts():
                post_type = post.get("post_type", post.get("badge", "커뮤니티"))
                if content_identity(post) in liked_ids and (post_type_filter is None or post_type == post_type_filter):
                    items.append(make_simple_content_item(
                        "community",
                        post.get("title", "커뮤니티 글"),
                        f'{post.get("category", "커뮤니티")} · {post_type}',
                        post.get("description", ""),
                        post_type,
                        post.get("meta", "댓글 0 · 저장 0"),
                        post,
                    ))
            return items

        if content_type in {"질문", "자유게시판"}:
            items = liked_community_items("자유" if content_type == "자유게시판" else content_type)
        elif content_type == "스냅":
            items = liked_snap_items()
        elif content_type == "비디오":
            items = liked_video_items()
        else:
            items = liked_community_items() + liked_snap_items() + liked_video_items()

        def content_tab(label):
            active = content_type == label
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=9),
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=lambda e, selected=label: show_liked_content_page(selected),
                ink=True,
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_800,
                ),
            )

        def open_item(item):
            def handler(e):
                source = item.get("source") or item
                if item["type"] == "snap":
                    open_snap_detail(source)
                elif item["type"] == "video":
                    show_video_detail_page(source)
                else:
                    open_content_detail(item, back_page="liked_content")
            return handler

        controls = [
            page_header("좋아요", on_back=go_back_page),
            ft.Text("좋아요를 누른 커뮤니티 글, 스냅, 비디오를 모아봤어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
            ft.Row(
                controls=[content_tab(label) for label in content_tabs],
                spacing=8,
                run_spacing=8,
                wrap=True,
                width=content_width(),
            ),
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
                            ft.Text("아직 좋아요 누른 글이 없어요.", size=15, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                            ft.Text("좋아요 버튼을 누르면 이곳에 모여요.", size=12, color=SUBTEXT_COLOR),
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
                open_reservation_entry()

        page.dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=22),
            title=ft.Text("예약을 취소할까요?", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            content=ft.Column(
                controls=[
                    ft.Text(f'{item.get("artist_name", "")} · {item.get("service", item.get("category", "기본 서비스"))}', size=13, color=TEXT_COLOR),
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
                    ft.Text("서비스 리뷰 작성", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=13, color=MAIN_COLOR),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        def _my_review_card(r):
            return review_display_card(r, show_admin_meta=False)

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
                        ft.Text("이용 후 느낀 점을 안전하게 남겨보세요.", size=12, color=SUBTEXT_COLOR),
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

    def show_review_admin_page():
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "review_admin"
        current_filter = app_state.get("review_admin_filter", "pending")
        reviews = [
            review
            for review in app_state.get("written_reviews", [])
            if current_filter == "all" or review.get("status", "visible") == current_filter
        ]
        reports = app_state.get("review_reports", [])

        def choose_filter(status):
            def handler(e):
                app_state["review_admin_filter"] = status
                show_review_admin_page()
            return handler

        def status_button(label, status, review_id, memo_getter):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=11, vertical=8),
                bgcolor=MAIN_COLOR_SOFT if status != "deleted" else "#FFF1F1",
                border_radius=999,
                border=ft.border.all(1, BORDER_COLOR),
                ink=True,
                on_click=lambda e: (
                    updateReviewStatus(review_id, status, memo_getter()),
                    show_snack("리뷰 상태가 변경되었어요."),
                    show_review_admin_page(),
                ),
                content=ft.Text(label, size=11, color=MAIN_COLOR_DARK if status != "deleted" else "#B85C5C", weight=ft.FontWeight.W_700),
            )

        def admin_review_card(review):
            review_id = review_identity(review)
            review_reports = [report for report in reports if report.get("reviewId") == review_id]
            memo_field = ft.TextField(
                width=content_width() - 44,
                value=review.get("adminMemo", ""),
                hint_text="관리자 메모",
                min_lines=1,
                max_lines=3,
                multiline=True,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                border_radius=RADIUS_MD,
            )
            report_text = "\n".join(
                [
                    f"- {report.get('reason', '')}: {report.get('detail', '') or '상세 없음'}"
                    for report in review_reports
                ]
            ) or "신고 사유 없음"
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
                    ft.Text(review.get("shopName", "방문 정보 없음"), size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                    ft.Text(review.get("artistName", review.get("artist_name", "공개 표시명")), size=11, color=SUBTEXT_COLOR),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                                review_status_chip(review.get("status", "visible")),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Text(
                            f"신고 {len(review_reports)}회 · 위험도 {review.get('riskScore', 0)} · {', '.join(review.get('detectedRiskTypes', [])) or '감지 없음'}",
                            size=11,
                            color=SUBTEXT_COLOR,
                        ),
                        ft.Text(review.get("reviewText", review.get("content", "")), size=13, color=TEXT_COLOR, height=1.45),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=10),
                            bgcolor=CHIP_BG,
                            border_radius=RADIUS_MD,
                            content=ft.Text(report_text, size=11, color=SUBTEXT_COLOR, height=1.45),
                        ),
                        memo_field,
                        ft.Row(
                            controls=[
                                status_button("숨김", "hidden", review_id, lambda field=memo_field: field.value or ""),
                                status_button("복구", "visible", review_id, lambda field=memo_field: field.value or ""),
                                status_button("삭제", "deleted", review_id, lambda field=memo_field: field.value or ""),
                            ],
                            spacing=8,
                            scroll=ft.ScrollMode.HIDDEN,
                        ),
                    ],
                    spacing=10,
                ),
            )

        filter_labels = [("전체", "all"), ("정상", "visible"), ("검토", "pending"), ("신고", "reported"), ("숨김", "hidden"), ("삭제", "deleted")]
        body_controls = [
            page_header("운영 검토", on_back=go_back_page),
            ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor=MAIN_COLOR_SOFT,
                border_radius=RADIUS_LG,
                border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
                content=ft.Text("신고된 리뷰와 검토 대기 리뷰를 확인하고 노출 상태를 관리해요.", size=12, color=TEXT_COLOR),
            ),
            ft.Row(
                controls=[community_chip(label, current_filter == key, choose_filter(key)) for label, key in filter_labels],
                spacing=8,
                scroll=ft.ScrollMode.HIDDEN,
            ),
            ft.Text(f"리뷰 {len(reviews)}개 · 신고 {len(reports)}건", size=12, color=SUBTEXT_COLOR, width=content_width()),
        ]
        if reviews:
            body_controls.extend([admin_review_card(review) for review in reviews])
        else:
            body_controls.append(
                ft.Container(
                    width=content_width(),
                    padding=SPACE_XL,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("현재 조건에 해당하는 리뷰가 없어요.", size=13, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            )
        body_controls.append(ft.Container(height=24))
        body = ft.Column(controls=body_controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
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
            ft.Text(f'서비스: {item.get("service", item.get("category", "기본 서비스"))}', size=12, color=TEXT_COLOR),
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
                "label": "프로필",
                "icon_name": "ACCOUNT_CIRCLE_OUTLINED",
                "action": lambda e: (close_overlays(), show_profile_page()),
                "enabled": True,
            },
            {
                "label": "나의 FINDY",
                "icon_name": "SPA_OUTLINED",
                "action": lambda e: (close_overlays(), show_beauty_profile_page()),
                "enabled": True,
            },
            {
                "label": "예약내역",
                "icon_name": "CALENDAR_MONTH",
                "action": lambda e: (close_overlays(), open_reservation_entry()),
                "enabled": True,
            },
            {
                "label": "완료한 이용",
                "icon_name": "CHECK_CIRCLE_OUTLINE",
                "action": lambda e: (close_overlays(), show_completed_page()),
                "enabled": True,
            },
            {
                "label": "취소된 이용",
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
                "action": lambda e: (close_overlays(), show_my_content_page("전체")),
                "enabled": True,
                "children": [
                    {"label": "전체", "action": lambda e: (close_overlays(), show_my_content_page("전체"))},
                    {"label": "질문", "action": lambda e: (close_overlays(), show_my_content_page("질문"))},
                    {"label": "자유게시판", "action": lambda e: (close_overlays(), show_my_content_page("자유게시판"))},
                    {"label": "스냅", "action": lambda e: (close_overlays(), show_my_content_page("스냅"))},
                    {"label": "비디오", "action": lambda e: (close_overlays(), show_my_content_page("비디오"))},
                ],
            },
            {
                "label": "좋아요",
                "icon_name": "FAVORITE_BORDER",
                "action": lambda e: (close_overlays(), show_liked_content_page("전체")),
                "enabled": True,
                "children": [
                    {"label": "전체", "action": lambda e: (close_overlays(), show_liked_content_page("전체"))},
                    {"label": "질문", "action": lambda e: (close_overlays(), show_liked_content_page("질문"))},
                    {"label": "자유게시판", "action": lambda e: (close_overlays(), show_liked_content_page("자유게시판"))},
                    {"label": "스냅", "action": lambda e: (close_overlays(), show_liked_content_page("스냅"))},
                    {"label": "비디오", "action": lambda e: (close_overlays(), show_liked_content_page("비디오"))},
                ],
            },
            {
                "label": "저장",
                "icon_name": "BOOKMARK_BORDER",
                "action": lambda e: (close_overlays(), show_saved_content_page("전체")),
                "enabled": True,
                "children": [
                    {"label": "전체", "action": lambda e: (close_overlays(), show_saved_content_page("전체"))},
                    {"label": "질문", "action": lambda e: (close_overlays(), show_saved_content_page("질문"))},
                    {"label": "자유게시판", "action": lambda e: (close_overlays(), show_saved_content_page("자유게시판"))},
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
                "예약과 이용 기록을 확인해보세요.",
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

        nav_controls = [
            nav_item("GROUP_OUTLINED", "GROUP", "커뮤니티", 0, open_left_menu),
            nav_item("PHOTO_LIBRARY_OUTLINED", "PHOTO_LIBRARY", "스냅", 1, go_snap_page),
            nav_item("HOME_OUTLINED", "HOME", "홈", 2, go_home_page),
            nav_item("SMART_DISPLAY_OUTLINED", "SMART_DISPLAY", "비디오", 3, go_video_page),
            nav_item("PERSON_OUTLINE", "PERSON", "내정보", 4, open_right_menu),
        ]

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

    def fixed_top_action_bar(current_page):
        unread_count = unread_notification_count()
        badge_text = "9+" if unread_count > 9 else str(unread_count)
        page_title = page_title_map().replace("FINDY ", "", 1).strip()
        compact_header = full_phone_width() < 340
        logo_width = 70 if compact_header else 98
        action_size = 28 if compact_header else 34
        action_icon_size = 20 if compact_header else 25
        logo_path = resolve_asset_file("app_logo/app_findy_logo_wordmark.png")
        logo = (
            ft.Image(src=logo_path, width=logo_width, height=24, fit=ft.ImageFit.CONTAIN)
            if logo_path
            else ft.Text("FINDY", size=20 if compact_header else 24, color=MAIN_COLOR, weight=ft.FontWeight.W_900)
        )

        def action_icon(icon_names, on_click, tooltip, badge=False):
            return ft.Container(
                width=action_size,
                height=action_size,
                border_radius=action_size / 2,
                alignment=ft.Alignment(0, 0),
                on_click=on_click,
                ink=True,
                tooltip=tooltip,
                content=ft.Stack(
                    controls=[
                        ft.Container(
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon(*icon_names), size=action_icon_size, color=TEXT_COLOR),
                        ),
                        ft.Container(
                            visible=badge and unread_count > 0,
                            right=0,
                            top=0,
                            width=18 if unread_count < 10 else 22,
                            height=18,
                            border_radius=999,
                            bgcolor="#D97757",
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(badge_text, size=9, color="#FFFFFF", weight=ft.FontWeight.W_900),
                        ),
                    ],
                ),
            )

        return ft.Container(
            left=0,
            right=0,
            top=0,
            height=64,
            padding=ft.padding.only(
                left=8 if compact_header else 22,
                right=8 if compact_header else 22,
                top=10,
                bottom=8,
            ),
            bgcolor=ft.Colors.with_opacity(0.98, BG_COLOR),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.55, BORDER_COLOR))),
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            logo,
                            ft.Text(
                                page_title,
                                size=16 if compact_header else 22,
                                color=TEXT_COLOR,
                                weight=ft.FontWeight.W_900,
                                visible=bool(page_title),
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=4 if compact_header else 8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            action_icon(("SEARCH", "SEARCH_OUTLINED"), lambda e: show_search_page(), "검색"),
                            action_icon(("SEND_OUTLINED", "NEAR_ME_OUTLINED"), lambda e: show_customer_messages_page(), "소식함"),
                            action_icon(("NOTIFICATIONS_OUTLINED", "NOTIFICATIONS", "NOTIFICATION_ADD"), open_notifications_page, "알림", badge=True),
                        ],
                        spacing=2 if compact_header else 10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=4 if compact_header else 12,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def render_phone_frame(body_content, nav_index=None):
        current_page = app_state.get("current_page", "home")
        if current_page not in public_pages and not app_state.get("current_user"):
            app_state["current_page"] = "login"
            app_state["page_history"] = []
            show_login_page()
            return
        last_page = app_state.get("_last_rendered_page")
        page_changed = current_page != last_page
        suppress_history_record = bool(app_state.pop("_suppress_next_history_record", False))
        auth_transition_pages = {"login", "signup", "opening"}
        auth_destination_pages = {"home"}
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
            "profile",
            "edit_profile",
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
            "liked_content",
            "content_detail",
            "community_board",
            "reservation_history",
            "cancelled_treatments",
            "my_reviews",
            "review_admin",
            "completed",
            "customer_messages",
            "message_detail",
            "beauty_profile",
            "findy_recommendation",
            "notice",
            "feedback",
            "support",
            "inquiry",
            "notifications",
            "settings",
            "placeholder_info",
        }
        full_height_pages = {"login", "signup", "account_recovery", "phone_onboarding"}
        has_fixed_top_bar = current_page not in {"opening", "login", "signup", "account_recovery", "phone_onboarding", "home_category_transition", "search"}
        content_top_padding = 64 if current_page == "video" else 76 if has_fixed_top_bar else 16
        nav_safe_bottom = (NAV_BAR_HEIGHT + NAV_SAFE_GAP) if nav_index is not None else 12
        nav_spacer = ft.Container(height=nav_safe_bottom)

        if current_page == "video":
            scroll_view = None
            body_wrapper = ft.Container(
                expand=True,
                padding=ft.padding.only(top=content_top_padding, bottom=0),
                content=body_content,
            )
        elif current_page in preserve_scroll_pages:
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
                padding=ft.padding.only(top=content_top_padding, bottom=8),
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
                padding=ft.padding.only(top=content_top_padding, bottom=8),
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
            height=full_phone_height(),
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
        if has_fixed_top_bar:
            stack_controls.append(fixed_top_action_bar(current_page))

        next_view = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=ft.Stack(
                width=full_phone_width(),
                height=full_phone_height(),
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
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
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
                "응대 스타일: 꼼꼼하고 친절한 느낌\n"
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
            add_boosted("a6", "응대 스타일을 중요하게 적어줘서 꼼꼼한 타입을 먼저 보여드려요.")
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
                            category_square("RATE_REVIEW", "리뷰", on_click_factory("리뷰")),
                            category_square("FORUM", "커뮤니티", on_click_factory("커뮤니티")),
                            category_square("CHAT_BUBBLE_OUTLINE", "자유게시판", on_click_factory("자유게시판")),
                        ],
                        spacing=slim_gap,
                    ),
                    ft.Row(
                        controls=[
                            category_square("PHOTO_LIBRARY", "스냅", on_click_factory("스냅")),
                            category_square("SMART_DISPLAY", "비디오", on_click_factory("비디오")),
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
            height=full_phone_height(),
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
            height=full_phone_height(),
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
            height=full_phone_height(),
            alignment=ft.Alignment(0, 0),
            content=opening_image,
            scale=1.04,
            animate_scale=ft.Animation(900, ft.AnimationCurve.EASE_OUT),
        )

        opening_overlay = ft.Container(
            width=full_phone_width(),
            height=full_phone_height(),
            bgcolor=ft.Colors.with_opacity(0.10, "#FFFFFF"),
            opacity=1.0,
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT),
        )

        opening_body = ft.Stack(
            controls=[
                ft.Container(
                    width=full_phone_width(),
                    height=full_phone_height(),
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
        if app_state.get("current_user"):
            show_home_page()
        else:
            show_login_page()

    def social_auth_buttons(error_text, policy_checkbox=None):
        button_width = max(126, (content_width() - 58) / 2)

        def social_button(provider_key):
            provider = SOCIAL_PROVIDERS[provider_key]
            return ft.Container(
                width=button_width,
                height=44,
                border_radius=15,
                bgcolor=provider["background"],
                border=ft.border.all(
                    1,
                    "#E4E4E4" if provider_key in {"google", "kakao"} else provider["background"],
                ),
                ink=True,
                on_click=lambda e, key=provider_key: page.run_task(
                    perform_social_auth,
                    key,
                    error_text,
                    policy_checkbox,
                ),
                content=ft.Row(
                    controls=[
                        ft.Image(
                            src=provider["asset"],
                            width=21,
                            height=21,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        ft.Text(
                            provider["label"],
                            size=12,
                            color=provider["foreground"],
                            weight=ft.FontWeight.W_800,
                        ),
                    ],
                    spacing=9,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[social_button("naver"), social_button("kakao")],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[social_button("google"), social_button("apple")],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    async def perform_social_auth(
        provider_key,
        error_text,
        policy_checkbox=None,
        link_current_account=False,
    ):
        if policy_checkbox is not None and not policy_checkbox.value:
            error_text.value = "이용약관과 개인정보 처리방침 동의가 필요합니다."
            page.update()
            return
        if app_state.get("_social_auth_busy"):
            show_snack("소셜 로그인을 진행 중이에요.")
            return
        if not social_auth_is_configured(FINDY2_AUTH_API_URL):
            error_text.value = "통합 로그인 서버 연결 전입니다. 개발자 설정이 필요해요."
            show_snack(
                "네이버·카카오·Google·Apple 앱 키와 FINDY 인증 서버 주소를 설정해주세요.",
                bgcolor="#B85C5C",
            )
            page.update()
            return

        app_state["_social_auth_busy"] = True
        provider_label = SOCIAL_PROVIDERS[provider_key]["label"]
        error_text.value = f"{provider_label} 로그인 페이지를 여는 중이에요."
        page.update()
        try:
            flow = await start_social_auth(
                FINDY2_AUTH_API_URL,
                provider_key,
                remote_session_token=read_remote_session_token(
                    FINDY2_SESSION_PATH
                ),
                link_account=link_current_account,
            )
            page.launch_url(flow.authorization_url)
            error_text.value = f"브라우저에서 {provider_label} 로그인을 완료해주세요."
            page.update()
            identity = await wait_for_social_auth(
                FINDY2_AUTH_API_URL,
                flow,
                timeout_seconds=FINDY2_SOCIAL_AUTH_TIMEOUT_SECONDS,
            )
            user = social_login_or_register(
                FINDY2_AUTH_DATA_PATH,
                identity,
                link_user_id=(
                    current_user_id()
                    if link_current_account
                    else None
                ),
            )
            if not user.get("phoneVerified"):
                app_state["pending_social_signup"] = {
                    "user": user,
                    "identity": identity,
                    "providerLabel": provider_label,
                }
                app_state["current_page"] = "phone_onboarding"
                show_phone_onboarding_page()
                return
            create_session(
                FINDY2_SESSION_PATH,
                user,
                remote_session_token=identity.get("findySessionToken"),
            )
            load_user_workspace(user)
            persist_user_data()
            app_state["selected_tab"] = 2
            if link_current_account:
                show_snack(f"{provider_label} 계정이 FINDY 통합회원에 연결됐어요.")
                app_state["selected_tab"] = 4
                show_connected_accounts_page()
            else:
                show_snack(f"{user['nickname']}님, {provider_label} 통합 로그인이 완료됐어요.")
                show_home_page()
        except (AuthError, SocialAuthError) as error:
            error_text.value = str(error)
            page.update()
        finally:
            app_state["_social_auth_busy"] = False

    def show_login_page():
        app_state["current_page"] = "login"

        def auth_field(label, hint, password=False):
            return ft.TextField(
                label=label,
                hint_text=hint,
                password=password,
                can_reveal_password=password,
                height=54,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                border_radius=17,
                bgcolor="#FFFFFF",
                text_style=ft.TextStyle(size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                label_style=ft.TextStyle(size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
            )

        phone_field = auth_field("휴대폰 번호", "010-1234-5678")
        password_field = auth_field("비밀번호", "영문과 숫자를 포함한 8자 이상", password=True)
        error_text = ft.Text("", size=11, color="#B85C5C", weight=ft.FontWeight.W_700)

        def submit_login(e=None):
            try:
                if (
                    FINDY2_DEMO_LOGIN_ENABLED
                    and not str(phone_field.value or "").strip()
                    and not str(password_field.value or "").strip()
                ):
                    user = get_or_create_demo_user(FINDY2_AUTH_DATA_PATH)
                else:
                    user = authenticate_user(
                        FINDY2_AUTH_DATA_PATH,
                        phone_field.value,
                        password_field.value,
                    )
                create_session(FINDY2_SESSION_PATH, user)
            except AuthError as error:
                error_text.value = str(error)
                page.update()
                return
            load_user_workspace(user)
            persist_user_data()
            app_state["selected_tab"] = 2
            show_snack(f"{user['nickname']}님, 반가워요.")
            show_home_page()

        password_field.on_submit = submit_login

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
            content=ft.Column(
                controls=[
                    login_logo_visual(148),
                    ft.Text("로그인", size=23, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                    ft.Text("나의 뷰티 기록과 커뮤니티 활동을 이어가세요.", size=11, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ft.Text(
                        "현재 테스트 버전은 입력 없이 로그인할 수 있어요.",
                        size=9,
                        color=MAIN_COLOR_DARK,
                        weight=ft.FontWeight.W_700,
                        visible=FINDY2_DEMO_LOGIN_ENABLED,
                    ),
                    ft.Container(height=4),
                    phone_field,
                    password_field,
                    error_text,
                    ft.Container(
                        width=288,
                        height=50,
                        bgcolor=MAIN_COLOR,
                        border_radius=17,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=submit_login,
                        content=ft.Text("로그인", size=15, color="#FFFFFF", weight=ft.FontWeight.W_900),
                    ),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                "가입 계정 확인",
                                on_click=lambda e: show_account_recovery_page("find_id"),
                                style=ft.ButtonStyle(
                                    color=SUBTEXT_COLOR,
                                    text_style=ft.TextStyle(size=10, weight=ft.FontWeight.W_700),
                                ),
                            ),
                            ft.Container(width=1, height=12, bgcolor=BORDER_COLOR),
                            ft.TextButton(
                                "비밀번호 재설정",
                                on_click=lambda e: show_account_recovery_page("reset_password"),
                                style=ft.ButtonStyle(
                                    color=SUBTEXT_COLOR,
                                    text_style=ft.TextStyle(size=10, weight=ft.FontWeight.W_700),
                                ),
                            ),
                        ],
                        spacing=2,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("아직 계정이 없나요?", size=11, color=SUBTEXT_COLOR),
                            ft.TextButton(
                                "회원가입",
                                on_click=lambda e: show_signup_page("user"),
                                style=ft.ButtonStyle(
                                    color=MAIN_COLOR_DARK,
                                    text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_900),
                                ),
                            ),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True),
                            ft.Text("통합회원 로그인", size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True),
                        ],
                        spacing=10,
                    ),
                    social_auth_buttons(error_text),
                    ft.Text(
                        "계속하면 이용약관과 개인정보 처리방침에 동의하는 것으로 봅니다.",
                        size=9,
                        color=SUBTEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
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
            alignment=ft.Alignment(0, 0),
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

    def show_account_recovery_page(mode="find_id"):
        mode = "reset_password" if mode == "reset_password" else "find_id"
        app_state["current_page"] = "account_recovery"
        app_state["account_recovery_mode"] = mode

        def recovery_field(label, hint, password=False):
            return ft.TextField(
                label=label,
                hint_text=hint,
                password=password,
                can_reveal_password=password,
                height=52,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                border_radius=16,
                bgcolor="#FFFFFF",
                text_style=ft.TextStyle(size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                label_style=ft.TextStyle(size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                content_padding=ft.padding.symmetric(horizontal=15, vertical=9),
            )

        phone_field = recovery_field("휴대폰 번호", "010-1234-5678")
        otp_field = recovery_field("인증번호", "문자로 받은 6자리 숫자")
        new_password_field = recovery_field(
            "새 비밀번호",
            "영문과 숫자를 포함한 8자 이상",
            password=True,
        )
        confirm_password_field = recovery_field(
            "새 비밀번호 확인",
            "비밀번호를 다시 입력해주세요.",
            password=True,
        )
        recovery_state = {
            "flow": None,
            "verified": False,
            "phone_number": "",
        }
        status_text = ft.Text(
            "PASS 본인확인 또는 문자 인증으로 계정을 안전하게 확인할 수 있어요.",
            size=10,
            color=SUBTEXT_COLOR,
            weight=ft.FontWeight.W_600,
        )
        result_column = ft.Column(spacing=8)

        def switch_mode(selected_mode):
            app_state["account_recovery_mode"] = selected_mode
            show_account_recovery_page(selected_mode)

        def mode_chip(label, value):
            active = mode == value
            return ft.Container(
                expand=True,
                height=42,
                border_radius=14,
                bgcolor=MAIN_COLOR if active else "#FFFFFF",
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda e: switch_mode(value),
                content=ft.Text(
                    label,
                    size=12,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_800,
                ),
            )

        def show_pass_information(e=None):
            status_text.value = (
                "PASS는 휴대폰 명의와 실제 사용자를 확인하는 강한 인증입니다. "
                "NICE·KCB·다날·KCP 등 본인확인기관 계약과 운영 키 발급 후 활성화됩니다."
            )
            status_text.color = MAIN_COLOR_DARK
            page.update()

        async def send_recovery_otp():
            recovery_state["verified"] = False
            result_column.controls = []
            status_text.value = "인증번호를 발송하는 중이에요."
            status_text.color = SUBTEXT_COLOR
            page.update()
            try:
                flow = await request_phone_otp(
                    FINDY2_AUTH_API_URL,
                    phone_field.value,
                    mode,
                )
                recovery_state["flow"] = flow
                status_text.value = f"{flow.masked_phone_number}로 인증번호를 보냈어요."
                status_text.color = MAIN_COLOR_DARK
            except PhoneAuthError as error:
                status_text.value = str(error)
                status_text.color = "#B85C5C"
            page.update()

        async def verify_recovery_otp():
            flow = recovery_state.get("flow")
            if not flow:
                status_text.value = "먼저 인증번호를 요청해주세요."
                status_text.color = "#B85C5C"
                page.update()
                return
            try:
                result = await verify_phone_otp(
                    FINDY2_AUTH_API_URL,
                    flow,
                    otp_field.value,
                )
                recovery_state["verified"] = True
                recovery_state["phone_number"] = result["phoneNumber"]
                phone_field.disabled = True
                otp_field.disabled = True
                status_text.value = "휴대폰 인증이 완료됐어요."
                status_text.color = "#4F8A5B"
                if mode == "find_id":
                    accounts = find_usernames_by_phone(
                        FINDY2_AUTH_DATA_PATH,
                        result["phoneNumber"],
                    )
                    if accounts:
                        result_column.controls = [
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                                bgcolor=MAIN_COLOR_SOFT,
                                border_radius=14,
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"가입 이름  {account['realName']}",
                                            size=12,
                                            color=TEXT_COLOR,
                                            weight=ft.FontWeight.W_800,
                                        ),
                                        ft.Text(
                                            "휴대폰 번호로 로그인할 수 있는 계정입니다.",
                                            size=10,
                                            color=SUBTEXT_COLOR,
                                        ),
                                    ],
                                    spacing=3,
                                ),
                            )
                            for account in accounts
                        ]
                    else:
                        result_column.controls = [
                            ft.Text(
                                "이 번호로 가입한 FINDY 계정을 찾지 못했어요.",
                                size=11,
                                color="#B85C5C",
                                weight=ft.FontWeight.W_700,
                            )
                        ]
            except (PhoneAuthError, AuthError) as error:
                status_text.value = str(error)
                status_text.color = "#B85C5C"
            page.update()

        def complete_password_reset(e=None):
            if not recovery_state.get("verified"):
                status_text.value = "먼저 휴대폰 인증을 완료해주세요."
                status_text.color = "#B85C5C"
                page.update()
                return
            if new_password_field.value != confirm_password_field.value:
                status_text.value = "새 비밀번호 확인이 일치하지 않습니다."
                status_text.color = "#B85C5C"
                page.update()
                return
            try:
                reset_password_by_phone(
                    FINDY2_AUTH_DATA_PATH,
                    recovery_state["phone_number"],
                    new_password_field.value,
                )
                show_snack("비밀번호를 새로 설정했어요. 다시 로그인해주세요.")
                show_login_page()
            except AuthError as error:
                status_text.value = str(error)
                status_text.color = "#B85C5C"
                page.update()

        card_controls = [
            login_logo_visual(116),
            ft.Text(
                "가입 계정 확인" if mode == "find_id" else "비밀번호 재설정",
                size=21,
                color=TEXT_COLOR,
                weight=ft.FontWeight.W_900,
            ),
            ft.Row(
                controls=[
                    mode_chip("가입 계정 확인", "find_id"),
                    mode_chip("비밀번호 재설정", "reset_password"),
                ],
                spacing=8,
            ),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                bgcolor=MAIN_COLOR_SOFT,
                border_radius=16,
                ink=True,
                on_click=show_pass_information,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon("VERIFIED_USER_OUTLINED", "SECURITY"), size=20, color=MAIN_COLOR_DARK),
                        ft.Column(
                            controls=[
                                ft.Text("PASS 본인확인", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                ft.Text("휴대폰 명의 확인 · 도입 준비", size=9, color=SUBTEXT_COLOR),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=14, color=SUBTEXT_COLOR),
                    ],
                    spacing=10,
                ),
            ),
            ft.Row(
                controls=[
                    ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True),
                    ft.Text("문자 인증", size=9, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                    ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True),
                ],
                spacing=8,
            ),
            phone_field,
            otp_field,
            ft.Row(
                controls=[
                    ft.Container(
                        expand=True,
                        height=42,
                        border_radius=14,
                        bgcolor=MAIN_COLOR_SOFT,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda e: page.run_task(send_recovery_otp),
                        content=ft.Text("인증번호 받기", size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                    ),
                    ft.Container(
                        expand=True,
                        height=42,
                        border_radius=14,
                        bgcolor="#FFFFFF",
                        border=ft.border.all(1, BORDER_COLOR),
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda e: page.run_task(verify_recovery_otp),
                        content=ft.Text("인증 확인", size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                    ),
                ],
                spacing=8,
            ),
            status_text,
            result_column,
        ]
        if mode == "reset_password":
            card_controls.extend(
                [
                    new_password_field,
                    confirm_password_field,
                    ft.Container(
                        width=288,
                        height=46,
                        bgcolor=MAIN_COLOR,
                        border_radius=16,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=complete_password_reset,
                        content=ft.Text("새 비밀번호 저장", size=13, color="#FFFFFF", weight=ft.FontWeight.W_900),
                    ),
                ]
            )

        card = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=24, vertical=22),
            bgcolor="#FFFFFF",
            border_radius=30,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=card_controls,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        body = ft.Container(
            expand=True,
            bgcolor="#FFFFFF",
            content=ft.Stack(
                controls=[
                    ft.ListView(
                        expand=True,
                        padding=ft.padding.only(left=16, right=16, top=34, bottom=28),
                        controls=[card],
                    ),
                    ft.Container(
                        left=18,
                        top=18,
                        content=ft.IconButton(
                            icon=app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"),
                            icon_color=TEXT_COLOR,
                            icon_size=20,
                            tooltip="로그인으로",
                            on_click=lambda e: show_login_page(),
                        ),
                    ),
                ],
            ),
        )
        render_phone_frame(body, None)

    def show_phone_onboarding_page():
        pending = app_state.get("pending_social_signup") or {}
        pending_user = pending.get("user") or {}
        identity = pending.get("identity") or {}
        if not pending_user:
            show_login_page()
            return
        app_state["current_page"] = "phone_onboarding"

        def onboarding_field(label, hint):
            return ft.TextField(
                label=label,
                hint_text=hint,
                height=52,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                border_radius=16,
                bgcolor="#FFFFFF",
                text_style=ft.TextStyle(size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                label_style=ft.TextStyle(size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                content_padding=ft.padding.symmetric(horizontal=15, vertical=9),
            )

        real_name_field = onboarding_field("이름(실명)", "한글 또는 영문 이름")
        phone_field = onboarding_field("휴대폰 번호", "010-1234-5678")
        otp_field = onboarding_field("인증번호", "문자로 받은 6자리 숫자")
        state = {"flow": None, "phoneNumber": "", "verified": False}
        status_text = ft.Text(
            "통합회원 가입을 마치려면 휴대폰 확인이 필요합니다.",
            size=10,
            color=SUBTEXT_COLOR,
            weight=ft.FontWeight.W_600,
        )

        async def send_otp():
            try:
                state["flow"] = await request_phone_otp(
                    FINDY2_AUTH_API_URL,
                    phone_field.value,
                    "signup",
                )
                status_text.value = f"{state['flow'].masked_phone_number}로 인증번호를 보냈어요."
                status_text.color = MAIN_COLOR_DARK
            except PhoneAuthError as error:
                status_text.value = str(error)
                status_text.color = "#B85C5C"
            page.update()

        async def verify_and_finish():
            if not state.get("flow"):
                status_text.value = "먼저 인증번호를 요청해주세요."
                status_text.color = "#B85C5C"
                page.update()
                return
            try:
                result = await verify_phone_otp(
                    FINDY2_AUTH_API_URL,
                    state["flow"],
                    otp_field.value,
                )
                user = attach_verified_phone(
                    FINDY2_AUTH_DATA_PATH,
                    pending_user["id"],
                    result["phoneNumber"],
                    verification_method="sms",
                    real_name=real_name_field.value,
                )
                create_session(
                    FINDY2_SESSION_PATH,
                    user,
                    remote_session_token=identity.get("findySessionToken"),
                )
                app_state.pop("pending_social_signup", None)
                load_user_workspace(user)
                persist_user_data()
                show_snack(f"{pending.get('providerLabel', '소셜')} 통합회원 가입이 완료됐어요.")
                show_home_page()
            except (PhoneAuthError, AuthError) as error:
                status_text.value = str(error)
                status_text.color = "#B85C5C"
                page.update()

        card = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=24, vertical=24),
            bgcolor="#FFFFFF",
            border_radius=30,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Column(
                controls=[
                    login_logo_visual(116),
                    ft.Text("통합회원 확인", size=21, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                    ft.Text(
                        f"{pending.get('providerLabel', '소셜')} 계정에 휴대폰 번호를 연결해주세요.",
                        size=10,
                        color=SUBTEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    real_name_field,
                    phone_field,
                    otp_field,
                    ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                height=42,
                                border_radius=14,
                                bgcolor=MAIN_COLOR_SOFT,
                                alignment=ft.Alignment(0, 0),
                                ink=True,
                                on_click=lambda e: page.run_task(send_otp),
                                content=ft.Text("인증번호 받기", size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                            ),
                            ft.Container(
                                expand=True,
                                height=42,
                                border_radius=14,
                                bgcolor=MAIN_COLOR,
                                alignment=ft.Alignment(0, 0),
                                ink=True,
                                on_click=lambda e: page.run_task(verify_and_finish),
                                content=ft.Text("가입 완료", size=11, color="#FFFFFF", weight=ft.FontWeight.W_900),
                            ),
                        ],
                        spacing=8,
                    ),
                    status_text,
                    ft.Text(
                        "이름은 가입 후 변경할 수 없고, 커뮤니티에는 소셜 프로필 닉네임만 표시됩니다.",
                        size=9,
                        color=SUBTEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        body = ft.Container(
            expand=True,
            bgcolor="#FFFFFF",
            content=ft.ListView(
                expand=True,
                padding=ft.padding.only(left=16, right=16, top=40, bottom=28),
                controls=[card],
            ),
        )
        render_phone_frame(body, None)

    def show_signup_page(role="user"):
        app_state["current_page"] = "signup"

        def signup_field(label, hint, password=False):
            return ft.TextField(
                label=label,
                hint_text=hint,
                password=password,
                can_reveal_password=password,
                height=52,
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                border_radius=16,
                bgcolor="#FFFFFF",
                text_style=ft.TextStyle(size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                label_style=ft.TextStyle(size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                content_padding=ft.padding.symmetric(horizontal=15, vertical=9),
            )

        real_name_field = signup_field("이름(실명)", "한글 또는 영문 이름")
        nickname_field = signup_field("닉네임", "커뮤니티에 표시할 이름")
        password_field = signup_field("비밀번호", "영문과 숫자를 포함한 8자 이상", password=True)
        confirm_field = signup_field("비밀번호 확인", "비밀번호를 다시 입력해주세요.", password=True)
        phone_field = signup_field("휴대폰 번호", "010-1234-5678")
        otp_field = signup_field("인증번호", "문자로 받은 6자리 숫자")
        phone_state = {
            "flow": None,
            "verified": False,
            "phone_number": "",
        }
        policy_agreed = ft.Checkbox(
            value=False,
            active_color=MAIN_COLOR,
            label="이용약관과 개인정보 처리방침에 동의합니다.",
            label_style=ft.TextStyle(size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
        )
        error_text = ft.Text("", size=11, color="#B85C5C", weight=ft.FontWeight.W_700)
        phone_status = ft.Text(
            "휴대폰 번호는 계정 찾기와 보안 알림에 사용됩니다.",
            size=9,
            color=SUBTEXT_COLOR,
            weight=ft.FontWeight.W_600,
        )

        async def send_signup_otp():
            phone_state["verified"] = False
            phone_status.value = "인증번호를 발송하는 중이에요."
            phone_status.color = SUBTEXT_COLOR
            page.update()
            try:
                flow = await request_phone_otp(
                    FINDY2_AUTH_API_URL,
                    phone_field.value,
                    "signup",
                )
                phone_state["flow"] = flow
                phone_status.value = f"{flow.masked_phone_number}로 인증번호를 보냈어요. 3분 안에 입력해주세요."
                phone_status.color = MAIN_COLOR_DARK
            except PhoneAuthError as error:
                phone_status.value = str(error)
                phone_status.color = "#B85C5C"
            page.update()

        async def confirm_signup_otp():
            flow = phone_state.get("flow")
            if not flow:
                phone_status.value = "먼저 인증번호를 요청해주세요."
                phone_status.color = "#B85C5C"
                page.update()
                return
            try:
                result = await verify_phone_otp(
                    FINDY2_AUTH_API_URL,
                    flow,
                    otp_field.value,
                )
                phone_state["verified"] = True
                phone_state["phone_number"] = result["phoneNumber"]
                phone_status.value = "휴대폰 인증이 완료됐어요."
                phone_status.color = "#4F8A5B"
                phone_field.disabled = True
                otp_field.disabled = True
            except PhoneAuthError as error:
                phone_status.value = str(error)
                phone_status.color = "#B85C5C"
            page.update()

        otp_actions = ft.Row(
            controls=[
                ft.Container(
                    expand=True,
                    height=42,
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=14,
                    alignment=ft.Alignment(0, 0),
                    ink=True,
                    on_click=lambda e: page.run_task(send_signup_otp),
                    content=ft.Text("인증번호 받기", size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                ),
                ft.Container(
                    expand=True,
                    height=42,
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, BORDER_COLOR),
                    border_radius=14,
                    alignment=ft.Alignment(0, 0),
                    ink=True,
                    on_click=lambda e: page.run_task(confirm_signup_otp),
                    content=ft.Text("인증 확인", size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                ),
            ],
            spacing=8,
        )

        def submit_signup(e=None):
            if password_field.value != confirm_field.value:
                error_text.value = "비밀번호 확인이 일치하지 않습니다."
                page.update()
                return
            if not policy_agreed.value:
                error_text.value = "이용약관과 개인정보 처리방침 동의가 필요합니다."
                page.update()
                return
            if not phone_state.get("verified"):
                error_text.value = "휴대폰 인증을 완료해주세요."
                page.update()
                return
            try:
                user = register_user(
                    FINDY2_AUTH_DATA_PATH,
                    "",
                    real_name_field.value,
                    nickname_field.value,
                    password_field.value,
                    phone_number=phone_state["phone_number"],
                    phone_verified=True,
                    phone_verification_method="sms",
                )
                create_session(FINDY2_SESSION_PATH, user)
            except AuthError as error:
                error_text.value = str(error)
                page.update()
                return
            load_user_workspace(user)
            persist_user_data()
            show_snack("FINDY2 가입이 완료되었어요.")
            show_home_page()

        confirm_field.on_submit = submit_signup

        card = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=24, vertical=22),
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
                    login_logo_visual(126),
                    ft.Text("회원가입", size=22, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
                    ft.Text("하나의 계정으로 글, 저장, 프로필을 안전하게 관리해요.", size=10, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    social_auth_buttons(error_text, policy_agreed),
                    ft.Row(
                        controls=[
                            ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True),
                            ft.Text("또는 휴대폰으로 가입", size=9, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True),
                        ],
                        spacing=8,
                    ),
                    real_name_field,
                    nickname_field,
                    phone_field,
                    otp_field,
                    otp_actions,
                    phone_status,
                    ft.Text(
                        "입력한 이름은 가입 후 변경할 수 없으며 공개 화면에는 닉네임만 표시됩니다.",
                        size=9,
                        color=SUBTEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    password_field,
                    confirm_field,
                    policy_agreed,
                    error_text,
                    ft.Container(
                        width=288,
                        height=48,
                        bgcolor=MAIN_COLOR,
                        border_radius=17,
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=submit_signup,
                        content=ft.Text("가입 완료", size=14, color="#FFFFFF", weight=ft.FontWeight.W_900),
                    ),
                ],
                spacing=8,
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
                        height=full_phone_height(),
                        alignment=ft.Alignment(0, 0),
                        content=ft.ListView(
                            expand=True,
                            padding=ft.padding.only(left=16, right=16, top=28, bottom=28),
                            controls=[card],
                        ),
                    ),
                    ft.Container(
                        left=20,
                        top=22,
                        content=ft.IconButton(
                            icon=app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"),
                            icon_color=TEXT_COLOR,
                            icon_size=20,
                            tooltip="뒤로가기",
                            on_click=lambda e: show_login_page(),
                        ),
                    ),
                ],
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

    def current_notification_items():
        items = community_notification_items()
        if FINDY2_RESERVATION_ENABLED:
            items.extend(reservation_notification_items())
        return sorted(items, key=lambda x: x["timestamp"], reverse=True)

    def community_notification_items():
        seed_time = app_state.setdefault("community_notification_seeded_at", datetime.now())
        notices = [
            {
                "id": "findy2_release_notice",
                "kind": "community",
                "title": "FINDY2 커뮤니티가 열렸어요",
                "body": "리뷰, 질문, 자유게시판에서 뷰티 경험을 먼저 모아볼게요.",
                "timestamp": seed_time - timedelta(minutes=5),
                "target_page": "category",
            },
            {
                "id": "findy_recommendation_notice",
                "kind": "recommendation",
                "title": "나의 FINDY를 채워보세요",
                "body": "관심 분야와 취향을 저장하면 추후 추천 정확도를 높일 수 있어요.",
                "timestamp": seed_time - timedelta(minutes=18),
                "target_page": "findy_recommendation",
            },
        ]

        if app_state.get("community_posts"):
            notices.append(
                {
                    "id": "community_activity_notice",
                    "kind": "community",
                    "title": "내 글에 새로운 반응이 있어요",
                    "body": "내가 쓴글에서 커뮤니티 활동을 확인해보세요.",
                    "timestamp": seed_time - timedelta(minutes=2),
                    "target_page": "my_content",
                }
            )
        if app_state.get("written_reviews"):
            notices.append(
                {
                    "id": "review_saved_notice",
                    "kind": "review",
                    "title": "리뷰가 저장되었어요",
                    "body": "내 후기에서 작성한 리뷰와 공개 상태를 확인할 수 있어요.",
                    "timestamp": seed_time - timedelta(minutes=8),
                    "target_page": "my_reviews",
                }
            )
        if app_state.get("written_videos"):
            notices.append(
                {
                    "id": "video_posted_notice",
                    "kind": "video",
                    "title": "비디오 팁이 게시되었어요",
                    "body": "FINDY 비디오에서 내가 올린 팁을 확인해보세요.",
                    "timestamp": seed_time - timedelta(minutes=12),
                    "target_page": "video",
                }
            )
        return notices

    def unread_notification_count():
        items = current_notification_items()
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
            open_reservation_entry()

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
        elif kind == "reservation":
            icon_name = "EVENT_AVAILABLE"
        elif kind == "review":
            icon_name = "RATE_REVIEW"
        elif kind == "video":
            icon_name = "SMART_DISPLAY_OUTLINED"
        elif kind == "recommendation":
            icon_name = "TUNE"
        elif kind in ("inquiry", "message"):
            icon_name = "CHAT_BUBBLE_OUTLINE"
        else:
            icon_name = "EVENT_BUSY"

        def open_notice_target(e=None):
            target_page = item.get("target_page")
            if target_page:
                app_state["current_page"] = target_page
                if target_page == "support":
                    app_state["selected_tab"] = 4
                render_current_page()
            elif kind == "review_request" and item.get("item"):
                app_state["review_target"] = item["item"]
                app_state["current_page"] = "write_review"
                render_current_page()
            elif item.get("item"):
                open_reservation_entry()

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
                                        ft.Text(item.get("artist_name", "취소된 이용"), size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
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
                                ft.Text(item.get("service", item.get("category", "기본 이용")), size=12, color=TEXT_COLOR),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            f"처리일: {event_at}" if event_at else "취소 또는 노쇼로 기록된 이용이에요.",
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
                            ft.Text("취소된 이용이 없어요", size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("취소와 노쇼 기록이 생기면 이곳에 정리돼요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ]

        body = ft.Column(
            controls=[
                page_header("취소된 이용", on_back=go_back_page),
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
                            "title": item.get("artist_name", "완료한 이용"),
                            "subtitle": item.get("job", ""),
                            "meta": f'{item.get("date", "")} · {item.get("time", "")}',
                            "description": f'이용 항목: {item.get("service", item.get("category", ""))}\n상태: 방문 완료',
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
                            ft.Text("아직 완료한 이용이 없어요.", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("예약을 진행하고 방문이 끝나면 이곳에 기록이 쌓여요.", size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=8,
                    ),
                )
            )

        body = ft.Column(
            controls=[
                page_header("완료한 이용", on_back=go_back_page),
                ft.Text("방문이 끝난 이용 기록을 모아볼 수 있어요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                *cards,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def default_user_profile():
        return {
            "name": "FINDY 회원",
            "username": "findy_user",
            "pronouns": "",
            "bio": "나에게 맞는 뷰티 스타일을 찾고 있어요.",
            "link": "",
            "banner": "",
            "gender": "선택 안 함",
            "profileCategory": "뷰티 관심 사용자",
            "contactOption": "비공개",
            "actionButton": "비활성화",
            "profileVisibility": "전체 공개",
            "facebook": "연결 안 됨",
            "interestedFields": ["메이크업", "헤어"],
            "styleKeywords": ["차가운", "귀여운"],
            "skinType": "지성",
            "makeupConcern": "지속력",
            "hairConcern": "볼륨",
            "personalTone": "쿨톤",
            "budgetRange": "상관없음",
            "locationPreference": "내 주변",
            "algorithmMemo": "관심 분야와 스타일에 맞춰 추천을 받고 싶어요.",
        }

    def get_user_profile():
        profile = app_state.setdefault("user_profile", default_user_profile())
        if app_state.get("current_user") and profile.get("name") == "FINDY 회원":
            profile["name"] = app_state["current_user"].get("nickname", "FINDY 회원")
        return profile

    def profile_avatar(size=82, profile=None):
        profile = profile or get_user_profile()
        label = profile.get("username") or profile.get("name") or "F"
        return ft.Container(
            width=size,
            height=size,
            border_radius=999,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, BORDER_COLOR),
            alignment=ft.Alignment(0, 0),
            content=ft.Text(":D" if size >= 72 else label[:1].upper(), size=24 if size >= 72 else 14, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
        )

    def profile_value_chip(value):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            bgcolor=CHIP_BG,
            border_radius=999,
            content=ft.Text(value, size=11, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
        )

    def show_profile_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "profile"

        profile = get_user_profile()
        posts_count = len(app_state.get("written_snaps", [])) + len(app_state.get("written_videos", [])) + len(app_state.get("community_posts", [])) + len(app_state.get("written_reviews", []))
        posts_count = max(posts_count, 9)
        fields = profile.get("interestedFields", [])
        styles = profile.get("styleKeywords", [])
        dashboard_text = f"{', '.join(fields[:2]) or '관심분야'} · {', '.join(styles[:2]) or '스타일'} · {profile.get('skinType', '피부타입')}"

        def stat_block(value, label):
            return ft.Container(
                expand=True,
                content=ft.Column(
                    controls=[
                        ft.Text(str(value), size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_900, text_align=ft.TextAlign.CENTER),
                        ft.Text(label, size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_700, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def profile_button(label, on_click):
            return ft.Container(
                expand=True,
                height=42,
                bgcolor=CHIP_BG,
                border_radius=8,
                alignment=ft.Alignment(0, 0),
                on_click=on_click,
                ink=True,
                content=ft.Text(label, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
            )

        def highlight(label, icon_name, on_click=None):
            return ft.Container(
                width=76,
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=58,
                            height=58,
                            border_radius=999,
                            bgcolor="#FFFFFF",
                            border=ft.border.all(1, BORDER_COLOR),
                            alignment=ft.Alignment(0, 0),
                            on_click=on_click,
                            ink=bool(on_click),
                            content=ft.Icon(app_icon(icon_name), size=26, color=TEXT_COLOR),
                        ),
                        ft.Text(label, size=11, color=TEXT_COLOR, weight=ft.FontWeight.W_700, max_lines=1, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def grid_tile(index):
            tile_size = (content_width() - 4) / 3
            return ft.Container(
                width=tile_size,
                height=tile_size,
                bgcolor="#000000",
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Stack(
                    controls=[
                        black_image_box(tile_size, tile_size),
                        ft.Container(
                            left=7,
                            bottom=7,
                            content=ft.Row(
                                controls=[
                                    ft.Icon(app_icon("REMOVE_RED_EYE_OUTLINED"), size=12, color="#FFFFFF"),
                                    ft.Text(["3,790", "1만", "8,388", "1.1만", "8,202", "621"][index % 6], size=10, color="#FFFFFF", weight=ft.FontWeight.W_800),
                                ],
                                spacing=4,
                            ),
                        ),
                        ft.Container(right=7, top=7, visible=index % 2 == 0, content=ft.Icon(app_icon("FILTER_NONE", "COPY_ALL"), size=16, color="#FFFFFF")),
                    ],
                ),
            )

        body = ft.Column(
            controls=[
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            ft.Container(width=34, height=34, border_radius=17, alignment=ft.Alignment(0, 0), on_click=lambda e: show_my_page(), ink=True, content=ft.Icon(app_icon("ARROW_BACK_IOS_NEW"), size=21, color=TEXT_COLOR)),
                            ft.Container(expand=True),
                            ft.Text(profile.get("username", "findy_user"), size=22, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                            ft.Icon(app_icon("KEYBOARD_ARROW_DOWN"), size=20, color=TEXT_COLOR),
                            ft.Container(width=8, height=8, border_radius=4, bgcolor=MAIN_COLOR),
                            ft.Container(expand=True),
                            ft.Icon(app_icon("ADD"), size=29, color=TEXT_COLOR),
                            ft.Icon(app_icon("MENU"), size=28, color=TEXT_COLOR),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.only(top=8),
                    content=ft.Row(
                        controls=[
                            ft.Stack(
                                controls=[
                                    profile_avatar(82, profile),
                                    ft.Container(right=0, bottom=0, width=26, height=26, border_radius=13, bgcolor=MAIN_COLOR, border=ft.border.all(2, "#FFFFFF"), alignment=ft.Alignment(0, 0), on_click=lambda e: show_edit_profile_page(reset_draft=True), ink=True, content=ft.Icon(app_icon("ADD"), size=18, color="#FFFFFF")),
                                ],
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(profile.get("name", "FINDY 회원"), size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                                    ft.Row(
                                        controls=[
                                            stat_block(posts_count, "게시물"),
                                            stat_block(profile.get("followers", "1,501"), "팔로워"),
                                            stat_block(profile.get("following", "511"), "팔로잉"),
                                        ],
                                        spacing=14,
                                    ),
                                ],
                                spacing=8,
                                expand=True,
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    content=ft.Column(
                        controls=[
                            ft.Text(profile.get("bio", ""), size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Text(profile.get("link", "") or "관심 링크를 추가해보세요.", size=12, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                            ft.Row(controls=[profile_value_chip(v) for v in (fields + styles)[:5]], spacing=6, wrap=True, run_spacing=6),
                        ],
                        spacing=7,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=14),
                    bgcolor=CHIP_BG,
                    border_radius=8,
                    content=ft.Column(
                        controls=[
                            ft.Text("FINDY 추천 대시보드", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                            ft.Text(dashboard_text, size=12, color=SUBTEXT_COLOR),
                        ],
                        spacing=3,
                    ),
                ),
                ft.Row(
                    width=content_width(),
                    controls=[
                        profile_button("프로필 편집", lambda e: show_edit_profile_page(reset_draft=True)),
                        profile_button("프로필 공유", lambda e: show_snack("프로필 공유 기능은 곧 연결될 예정이에요.")),
                    ],
                    spacing=6,
                ),
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            highlight("New", "ADD", lambda e: show_write_snap_page()),
                            highlight("하이라이트", "AUTO_AWESOME"),
                            highlight("관심분야", "SPA_OUTLINED", lambda e: show_findy_recommendation_page(reset_draft=True)),
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.HIDDEN,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            ft.Container(expand=True, height=44, alignment=ft.Alignment(0, 0), border=ft.border.only(bottom=ft.BorderSide(2, TEXT_COLOR)), content=ft.Icon(app_icon("GRID_ON"), size=25, color=TEXT_COLOR)),
                            ft.Container(expand=True, height=44, alignment=ft.Alignment(0, 0), content=ft.Icon(app_icon("SMART_DISPLAY_OUTLINED"), size=25, color=SUBTEXT_COLOR)),
                            ft.Container(expand=True, height=44, alignment=ft.Alignment(0, 0), content=ft.Icon(app_icon("AUTORENEW"), size=25, color=SUBTEXT_COLOR)),
                            ft.Container(expand=True, height=44, alignment=ft.Alignment(0, 0), content=ft.Icon(app_icon("PERSON_PIN_OUTLINED"), size=25, color=SUBTEXT_COLOR)),
                        ],
                    ),
                ),
                ft.Container(width=content_width(), content=ft.Row(controls=[grid_tile(i) for i in range(6)], spacing=2, run_spacing=2, wrap=True)),
                ft.Container(height=24),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_edit_profile_page(reset_draft=False):
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "edit_profile"

        if reset_draft or app_state.get("profile_edit_draft") is None:
            app_state["profile_edit_draft"] = json.loads(json.dumps(get_user_profile()))
        draft = app_state["profile_edit_draft"]
        recommendation_categories = ["헤어", "네일아트", "메이크업", "포토", "웨딩", "반영구시술"]
        recommendation_slug_map = {
            "헤어": "hair",
            "네일아트": "nail",
            "메이크업": "makeup",
            "포토": "photo",
            "웨딩": "wedding",
            "반영구시술": "semi_permanent",
        }
        selected_recommendation_fields = draft.setdefault("interestedFields", ["헤어"])
        active_recommendation_category = app_state.get("profile_edit_active_category") or (selected_recommendation_fields[0] if selected_recommendation_fields else "헤어")
        if active_recommendation_category not in recommendation_categories:
            active_recommendation_category = "헤어"
        if active_recommendation_category not in selected_recommendation_fields:
            selected_recommendation_fields.append(active_recommendation_category)
        app_state["profile_edit_active_category"] = active_recommendation_category

        def recommendation_key(key, category=None):
            slug = recommendation_slug_map.get(category or active_recommendation_category, "hair")
            return f"{key}_{slug}"

        def seed_recommendation_defaults():
            for category in recommendation_categories:
                style_key = recommendation_key("styleKeywords", category)
                if style_key not in draft:
                    draft[style_key] = list(draft.get("styleKeywords", [])) if category == active_recommendation_category else []
                for base_key in ["budgetRange", "locationPreference", "algorithmMemo"]:
                    scoped = recommendation_key(base_key, category)
                    if scoped not in draft:
                        draft[scoped] = draft.get(base_key, "")
            draft.setdefault(recommendation_key("hairConcern", "헤어"), draft.get("hairConcern", ""))
            draft.setdefault(recommendation_key("skinType", "메이크업"), draft.get("skinType", ""))
            draft.setdefault(recommendation_key("makeupConcern", "메이크업"), draft.get("makeupConcern", ""))
            draft.setdefault(recommendation_key("personalTone", "메이크업"), draft.get("personalTone", ""))

        seed_recommendation_defaults()

        def update_field(key):
            def handler(e):
                draft[key] = e.control.value or ""
            return handler

        def save_profile(e=None):
            profile = json.loads(json.dumps(draft))
            active = app_state.get("profile_edit_active_category", active_recommendation_category)
            profile["styleKeywords"] = list(profile.get(recommendation_key("styleKeywords", active), profile.get("styleKeywords", [])))
            profile["budgetRange"] = profile.get(recommendation_key("budgetRange", active), profile.get("budgetRange", ""))
            profile["locationPreference"] = profile.get(recommendation_key("locationPreference", active), profile.get("locationPreference", ""))
            profile["algorithmMemo"] = profile.get(recommendation_key("algorithmMemo", active), profile.get("algorithmMemo", ""))
            recommendation_by_category = {}
            for category in recommendation_categories:
                suffix = f"_{recommendation_slug_map[category]}"
                category_data = {}
                for key, value in profile.items():
                    if key.endswith(suffix):
                        category_data[key[: -len(suffix)]] = value
                recommendation_by_category[category] = category_data
            profile["recommendationByCategory"] = recommendation_by_category
            if not sync_profile_to_auth(profile):
                return
            app_state["user_profile"] = profile
            app_state["profile_edit_draft"] = None
            if app_state.get("current_user"):
                app_state["current_user"]["nickname"] = profile.get("name") or profile.get("username") or "FINDY 회원"
            persist_user_data(notify_on_error=True)
            show_snack("프로필이 저장되었어요.")
            show_profile_page()

        def edit_text_row(label, key, hint="", multiline=False):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=11),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Row(
                    controls=[
                        ft.Text(label, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800, width=112),
                        ft.TextField(
                            value=draft.get(key, ""),
                            hint_text=hint,
                            border=ft.InputBorder.NONE,
                            multiline=multiline,
                            min_lines=1,
                            max_lines=3 if multiline else 1,
                            text_style=ft.TextStyle(size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
                            on_change=update_field(key),
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            )

        def single_choice_row(title, key, options):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=13),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(title, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, width=112),
                                ft.Text(draft.get(key, ""), size=12, color=SUBTEXT_COLOR, expand=True),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                community_chip(option, draft.get(key) == option, lambda e, opt=option: (draft.__setitem__(key, opt), show_edit_profile_page()))
                                for option in options
                            ],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=9,
                ),
            )

        def multi_choice_row(title, key, options):
            values = draft.setdefault(key, [])

            def toggle(option):
                def handler(e):
                    current = draft.setdefault(key, [])
                    if option in current:
                        current.remove(option)
                    else:
                        current.append(option)
                    show_edit_profile_page()
                return handler

            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=13),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ft.Row(
                            controls=[community_chip(option, option in values, toggle(option)) for option in options],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=9,
                ),
            )

        def recommendation_category_row():
            values = draft.setdefault("interestedFields", [])

            def choose(category):
                def handler(e):
                    if category not in values:
                        values.append(category)
                    app_state["profile_edit_active_category"] = category
                    show_edit_profile_page()
                return handler

            def category_chip(category):
                active = category == active_recommendation_category
                selected = category in values
                return ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    bgcolor=MAIN_COLOR if active else MAIN_COLOR_SOFT if selected else "#FFFFFF",
                    border_radius=999,
                    border=ft.border.all(1, MAIN_COLOR if active or selected else BORDER_COLOR),
                    on_click=choose(category),
                    ink=True,
                    content=ft.Text(
                        category,
                        size=13,
                        color="#FFFFFF" if active else TEXT_COLOR,
                        weight=ft.FontWeight.W_800,
                    ),
                )

            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=13),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("관심있는 분야", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True),
                                ft.Text(f"{active_recommendation_category} 편집 중", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[category_chip(category) for category in recommendation_categories],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=9,
                ),
            )

        style_options_by_category = {
            "헤어": ["내추럴", "차분한", "힙한", "고급스러운", "러블리", "시크한", "청순한", "화려한"],
            "네일아트": ["깔끔한", "시럽", "프렌치", "글리터", "귀여운", "화려한", "오피스", "웨딩"],
            "메이크업": ["차가운", "귀여운", "도도한", "내추럴", "화려한", "청순한", "힙한", "고급스러운"],
            "포토": ["자연스러운", "고급스러운", "청량한", "시크한", "따뜻한", "필름감성", "화보느낌", "보정 적게"],
            "웨딩": ["자연스러운", "화사한", "우아한", "고급스러운", "깔끔한", "러블리", "클래식", "화려한"],
            "반영구시술": ["자연스러운", "또렷한", "깔끔한", "부드러운", "대칭감", "민낯 친화", "선명한", "은은한"],
        }
        budget_options_by_category = {
            "헤어": ["상관없음", "5만원 이하", "5~10만원", "10~20만원", "20만원 이상", "가성비", "프리미엄"],
            "네일아트": ["상관없음", "3만원 이하", "3~5만원", "5~8만원", "8만원 이상", "가성비", "프리미엄"],
            "메이크업": ["상관없음", "5만원 이하", "5~10만원", "10~20만원", "20만원 이상", "가성비", "프리미엄"],
            "포토": ["상관없음", "10만원 이하", "10~20만원", "20~40만원", "40만원 이상", "가성비", "프리미엄"],
            "웨딩": ["상관없음", "20만원 이하", "20~50만원", "50~100만원", "100만원 이상", "가성비", "프리미엄"],
            "반영구시술": ["상관없음", "10만원 이하", "10~20만원", "20~40만원", "40만원 이상", "가성비", "프리미엄"],
        }

        def recommendation_rows():
            category = active_recommendation_category
            common_rows = [
                multi_choice_row("선호 스타일", recommendation_key("styleKeywords"), style_options_by_category.get(category, [])),
            ]
            category_rows = {
                "헤어": [
                    single_choice_row("헤어 고민", recommendation_key("hairConcern"), ["볼륨", "손상모", "곱슬", "탈색모", "두피", "숱 적음", "숱 많음"]),
                    single_choice_row("헤어 목적", recommendation_key("visitPurpose"), ["데일리 관리", "기분전환", "촬영", "데이트", "면접", "웨딩", "여행"]),
                ],
                "네일아트": [
                    single_choice_row("네일 고민", recommendation_key("nailConcern"), ["손톱 얇음", "잘 부러짐", "유지력", "큐티클", "짧은 손톱", "파츠 유지"]),
                    single_choice_row("네일 목적", recommendation_key("visitPurpose"), ["데일리", "기분전환", "여행", "촬영", "웨딩", "계절 아트"]),
                ],
                "메이크업": [
                    single_choice_row("피부/메이크업", recommendation_key("skinType"), ["지성", "건성", "복합성", "민감성", "수부지"]),
                    single_choice_row("메이크업 고민", recommendation_key("makeupConcern"), ["지속력", "커버력", "톤보정", "무너짐", "모공", "다크닝", "건조 끼임"]),
                    single_choice_row("퍼스널 톤", recommendation_key("personalTone"), ["웜톤", "쿨톤", "뉴트럴", "잘 모름"]),
                ],
                "포토": [
                    single_choice_row("포토 목적", recommendation_key("photoPurpose"), ["프로필", "증명사진", "SNS", "커플", "우정", "가족", "웨딩 스냅"]),
                    single_choice_row("포토 무드", recommendation_key("photoMood"), ["자연스러운", "고급스러운", "청량한", "시크한", "따뜻한", "필름감성"]),
                ],
                "웨딩": [
                    single_choice_row("웨딩 역할", recommendation_key("weddingRole"), ["신부", "신랑", "혼주", "하객", "브라이덜샤워", "스몰웨딩"]),
                    single_choice_row("웨딩 니즈", recommendation_key("weddingNeed"), ["오래 유지", "사진발", "눈물/땀 걱정", "자연스러운", "화려한", "피부관리 포함"]),
                ],
                "반영구시술": [
                    single_choice_row("시술 부위", recommendation_key("semiPermanentArea"), ["눈썹", "아이라인", "입술", "헤어라인", "두피 SMP"]),
                    single_choice_row("반영구 고민", recommendation_key("semiPermanentConcern"), ["자연스러운 색", "또렷한 라인", "탈각 걱정", "붓기 걱정", "통증 걱정", "색 빠짐"]),
                ],
            }
            return [
                ft.Container(width=content_width(), padding=ft.padding.only(top=4), content=ft.Text(f"{category} 추천 항목", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900)),
                *common_rows,
                *category_rows.get(category, []),
                single_choice_row("예산", recommendation_key("budgetRange"), budget_options_by_category.get(category, ["상관없음", "가성비", "중간", "프리미엄"])),
                single_choice_row("추천 위치", recommendation_key("locationPreference"), ["내 주변", "인기 지역", "상관없음"]),
                edit_text_row("알고리즘 메모", recommendation_key("algorithmMemo"), f"{category} 추천에 반영할 취향을 적어주세요.", multiline=True),
            ]

        body = ft.Column(
            controls=[
                ft.Container(
                    width=content_width(),
                    height=52,
                    content=ft.Row(
                        controls=[
                            ft.Container(width=42, height=42, border_radius=21, bgcolor="#FFFFFF", alignment=ft.Alignment(0, 0), on_click=lambda e: show_profile_page(), ink=True, content=ft.Icon(app_icon("ARROW_BACK_IOS_NEW"), size=22, color=TEXT_COLOR)),
                            ft.Text("프로필 편집", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True, text_align=ft.TextAlign.CENTER),
                            ft.Container(width=42, height=42, border_radius=21, alignment=ft.Alignment(0, 0), on_click=save_profile, ink=True, content=ft.Text("저장", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_900)),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(vertical=18),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        controls=[
                            profile_avatar(92, draft),
                            ft.Text("사진 또는 아바타 수정", size=13, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_900),
                        ],
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=14, vertical=13),
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=16,
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("가입 이름", size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                    ft.Text(
                                        (app_state.get("current_user") or {}).get("realName")
                                        or draft.get("realName")
                                        or "등록된 이름 없음",
                                        size=13,
                                        color=TEXT_COLOR,
                                        weight=ft.FontWeight.W_900,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                bgcolor="#FFFFFF",
                                border_radius=999,
                                content=ft.Text("수정 불가", size=9, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                            ),
                        ],
                    ),
                ),
                edit_text_row("닉네임", "name", "커뮤니티에 표시할 이름"),
                edit_text_row("성별 대명사", "pronouns", "성별 대명사"),
                edit_text_row("소개", "bio", "Ch.2", multiline=True),
                edit_text_row("링크", "link", "youtube.com/..."),
                edit_text_row("배너", "banner", "음악, 프로필 등을 추가해보세요."),
                single_choice_row("그리드 순서 변경", "gridOrder", ["최신순", "인기순", "새 알림"]),
                single_choice_row("성별", "gender", ["여성", "남성", "선택 안 함"]),
                ft.Container(width=content_width(), padding=ft.padding.only(top=10), content=ft.Text("프로필 정보", size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_900)),
                single_choice_row("Facebook", "facebook", ["연결", "연결 안 됨"]),
                single_choice_row("카테고리", "profileCategory", ["뷰티 관심 사용자", "디지털 크리에이터", "리뷰어", "스냅러"]),
                single_choice_row("연락처 옵션", "contactOption", ["비공개", "이메일만", "앱 알림만"]),
                single_choice_row("행동 유도 버튼", "actionButton", ["비활성화", "팔로우", "문의하기"]),
                single_choice_row("프로필 표시", "profileVisibility", ["전체 공개", "팔로워만", "비공개"]),
                soft_button("프로필 저장", MAIN_COLOR, "white", save_profile, width=content_width()),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_findy_recommendation_page(reset_draft=False):
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "findy_recommendation"

        if reset_draft or app_state.get("findy_recommendation_draft") is None:
            app_state["findy_recommendation_draft"] = json.loads(json.dumps(get_user_profile()))
        draft = app_state["findy_recommendation_draft"]

        recommendation_categories = ["헤어", "네일아트", "메이크업", "포토", "웨딩", "반영구시술"]
        recommendation_slug_map = {
            "헤어": "hair",
            "네일아트": "nail",
            "메이크업": "makeup",
            "포토": "photo",
            "웨딩": "wedding",
            "반영구시술": "semi_permanent",
        }
        selected_fields = draft.setdefault("interestedFields", ["헤어"])
        active_category = app_state.get("findy_recommendation_active_category") or (selected_fields[0] if selected_fields else "헤어")
        if active_category not in recommendation_categories:
            active_category = "헤어"
        if active_category not in selected_fields:
            selected_fields.append(active_category)
        app_state["findy_recommendation_active_category"] = active_category

        def recommendation_key(key, category=None):
            slug = recommendation_slug_map.get(category or active_category, "hair")
            return f"{key}_{slug}"

        def seed_recommendation_defaults():
            for category in recommendation_categories:
                style_key = recommendation_key("styleKeywords", category)
                if style_key not in draft:
                    draft[style_key] = list(draft.get("styleKeywords", [])) if category == active_category else []
                for base_key in ["budgetRange", "locationPreference", "algorithmMemo"]:
                    scoped = recommendation_key(base_key, category)
                    if scoped not in draft:
                        draft[scoped] = draft.get(base_key, "")
            draft.setdefault(recommendation_key("hairConcern", "헤어"), draft.get("hairConcern", ""))
            draft.setdefault(recommendation_key("skinType", "메이크업"), draft.get("skinType", ""))
            draft.setdefault(recommendation_key("makeupConcern", "메이크업"), draft.get("makeupConcern", ""))
            draft.setdefault(recommendation_key("personalTone", "메이크업"), draft.get("personalTone", ""))

        seed_recommendation_defaults()

        def update_field(key):
            def handler(e):
                draft[key] = e.control.value or ""
            return handler

        def refresh_recommendation_page():
            show_findy_recommendation_page()

        def save_recommendation(e=None):
            profile = json.loads(json.dumps(get_user_profile()))
            profile["interestedFields"] = list(draft.get("interestedFields", []))
            for category in recommendation_categories:
                suffix = f"_{recommendation_slug_map[category]}"
                for key, value in draft.items():
                    if key.endswith(suffix):
                        profile[key] = value

            active = app_state.get("findy_recommendation_active_category", active_category)
            profile["styleKeywords"] = list(profile.get(recommendation_key("styleKeywords", active), profile.get("styleKeywords", [])))
            profile["budgetRange"] = profile.get(recommendation_key("budgetRange", active), profile.get("budgetRange", ""))
            profile["locationPreference"] = profile.get(recommendation_key("locationPreference", active), profile.get("locationPreference", ""))
            profile["algorithmMemo"] = profile.get(recommendation_key("algorithmMemo", active), profile.get("algorithmMemo", ""))

            recommendation_by_category = {}
            for category in recommendation_categories:
                suffix = f"_{recommendation_slug_map[category]}"
                category_data = {}
                for key, value in profile.items():
                    if key.endswith(suffix):
                        category_data[key[: -len(suffix)]] = value
                recommendation_by_category[category] = category_data
            profile["recommendationByCategory"] = recommendation_by_category

            if not sync_profile_to_auth(profile):
                return
            app_state["user_profile"] = profile
            app_state["findy_recommendation_draft"] = None
            persist_user_data(notify_on_error=True)
            show_snack("FINDY 추천정보가 저장되었어요.")
            show_my_page()

        def edit_text_row(label, key, hint="", multiline=False):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=11),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Row(
                    controls=[
                        ft.Text(label, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800, width=112),
                        ft.TextField(
                            value=draft.get(key, ""),
                            hint_text=hint,
                            border=ft.InputBorder.NONE,
                            multiline=multiline,
                            min_lines=1,
                            max_lines=3 if multiline else 1,
                            text_style=ft.TextStyle(size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            hint_style=ft.TextStyle(size=13, color=SUBTEXT_COLOR),
                            on_change=update_field(key),
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            )

        def single_choice_row(title, key, options):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=13),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(title, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, width=112),
                                ft.Text(draft.get(key, ""), size=12, color=SUBTEXT_COLOR, expand=True),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                community_chip(option, draft.get(key) == option, lambda e, opt=option: (draft.__setitem__(key, opt), refresh_recommendation_page()))
                                for option in options
                            ],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=9,
                ),
            )

        def multi_choice_row(title, key, options):
            values = draft.setdefault(key, [])

            def toggle(option):
                def handler(e):
                    current = draft.setdefault(key, [])
                    if option in current:
                        current.remove(option)
                    else:
                        current.append(option)
                    refresh_recommendation_page()
                return handler

            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=13),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ft.Row(
                            controls=[community_chip(option, option in values, toggle(option)) for option in options],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=9,
                ),
            )

        def recommendation_category_row():
            values = draft.setdefault("interestedFields", [])

            def choose(category):
                def handler(e):
                    if category not in values:
                        values.append(category)
                    app_state["findy_recommendation_active_category"] = category
                    refresh_recommendation_page()
                return handler

            def category_chip(category):
                active = category == active_category
                selected = category in values
                return ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    bgcolor=MAIN_COLOR if active else MAIN_COLOR_SOFT if selected else "#FFFFFF",
                    border_radius=999,
                    border=ft.border.all(1, MAIN_COLOR if active or selected else BORDER_COLOR),
                    on_click=choose(category),
                    ink=True,
                    content=ft.Text(
                        category,
                        size=13,
                        color="#FFFFFF" if active else TEXT_COLOR,
                        weight=ft.FontWeight.W_800,
                    ),
                )

            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(vertical=13),
                border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("관심있는 분야", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True),
                                ft.Text(f"{active_category} 편집 중", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[category_chip(category) for category in recommendation_categories],
                            spacing=7,
                            run_spacing=7,
                            wrap=True,
                        ),
                    ],
                    spacing=9,
                ),
            )

        style_options_by_category = {
            "헤어": ["내추럴", "차분한", "힙한", "고급스러운", "러블리", "시크한", "청순한", "화려한"],
            "네일아트": ["깔끔한", "시럽", "프렌치", "글리터", "귀여운", "화려한", "오피스", "웨딩"],
            "메이크업": ["차가운", "귀여운", "도도한", "내추럴", "화려한", "청순한", "힙한", "고급스러운"],
            "포토": ["자연스러운", "고급스러운", "청량한", "시크한", "따뜻한", "필름감성", "화보느낌", "보정 적게"],
            "웨딩": ["자연스러운", "화사한", "우아한", "고급스러운", "깔끔한", "러블리", "클래식", "화려한"],
            "반영구시술": ["자연스러운", "또렷한", "깔끔한", "부드러운", "대칭감", "민낯 친화", "선명한", "은은한"],
        }
        budget_options_by_category = {
            "헤어": ["상관없음", "5만원 이하", "5~10만원", "10~20만원", "20만원 이상", "가성비", "프리미엄"],
            "네일아트": ["상관없음", "3만원 이하", "3~5만원", "5~8만원", "8만원 이상", "가성비", "프리미엄"],
            "메이크업": ["상관없음", "5만원 이하", "5~10만원", "10~20만원", "20만원 이상", "가성비", "프리미엄"],
            "포토": ["상관없음", "10만원 이하", "10~20만원", "20~40만원", "40만원 이상", "가성비", "프리미엄"],
            "웨딩": ["상관없음", "20만원 이하", "20~50만원", "50~100만원", "100만원 이상", "가성비", "프리미엄"],
            "반영구시술": ["상관없음", "10만원 이하", "10~20만원", "20~40만원", "40만원 이상", "가성비", "프리미엄"],
        }

        def recommendation_rows():
            category_rows = {
                "헤어": [
                    single_choice_row("헤어 고민", recommendation_key("hairConcern"), ["볼륨", "손상모", "곱슬", "탈색모", "두피", "숱 적음", "숱 많음"]),
                    single_choice_row("헤어 목적", recommendation_key("visitPurpose"), ["데일리 관리", "기분전환", "촬영", "데이트", "면접", "웨딩", "여행"]),
                ],
                "네일아트": [
                    single_choice_row("네일 고민", recommendation_key("nailConcern"), ["손톱 얇음", "잘 부러짐", "유지력", "큐티클", "짧은 손톱", "파츠 유지"]),
                    single_choice_row("네일 목적", recommendation_key("visitPurpose"), ["데일리", "기분전환", "여행", "촬영", "웨딩", "계절 아트"]),
                ],
                "메이크업": [
                    single_choice_row("피부/메이크업", recommendation_key("skinType"), ["지성", "건성", "복합성", "민감성", "수부지"]),
                    single_choice_row("메이크업 고민", recommendation_key("makeupConcern"), ["지속력", "커버력", "톤보정", "무너짐", "모공", "다크닝", "건조 끼임"]),
                    single_choice_row("퍼스널 톤", recommendation_key("personalTone"), ["웜톤", "쿨톤", "뉴트럴", "잘 모름"]),
                ],
                "포토": [
                    single_choice_row("포토 목적", recommendation_key("photoPurpose"), ["프로필", "증명사진", "SNS", "커플", "우정", "가족", "웨딩 스냅"]),
                    single_choice_row("포토 무드", recommendation_key("photoMood"), ["자연스러운", "고급스러운", "청량한", "시크한", "따뜻한", "필름감성"]),
                ],
                "웨딩": [
                    single_choice_row("웨딩 역할", recommendation_key("weddingRole"), ["신부", "신랑", "혼주", "하객", "브라이덜샤워", "스몰웨딩"]),
                    single_choice_row("웨딩 니즈", recommendation_key("weddingNeed"), ["오래 유지", "사진발", "눈물/땀 걱정", "자연스러운", "화려한", "피부관리 포함"]),
                ],
                "반영구시술": [
                    single_choice_row("시술 부위", recommendation_key("semiPermanentArea"), ["눈썹", "아이라인", "입술", "헤어라인", "두피 SMP"]),
                    single_choice_row("반영구 고민", recommendation_key("semiPermanentConcern"), ["자연스러운 색", "또렷한 라인", "탈각 걱정", "붓기 걱정", "통증 걱정", "색 빠짐"]),
                ],
            }
            return [
                ft.Container(width=content_width(), padding=ft.padding.only(top=4), content=ft.Text(f"{active_category} 추천 항목", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900)),
                multi_choice_row("선호 스타일", recommendation_key("styleKeywords"), style_options_by_category.get(active_category, [])),
                *category_rows.get(active_category, []),
                single_choice_row("예산", recommendation_key("budgetRange"), budget_options_by_category.get(active_category, ["상관없음", "가성비", "중간", "프리미엄"])),
                single_choice_row("추천 위치", recommendation_key("locationPreference"), ["내 주변", "인기 지역", "상관없음"]),
                edit_text_row("알고리즘 메모", recommendation_key("algorithmMemo"), f"{active_category} 추천에 반영할 취향을 적어주세요.", multiline=True),
            ]

        body = ft.Column(
            controls=[
                page_header("FINDY 추천정보", on_back=go_back_page),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=14),
                    bgcolor="#FFFFFF",
                    border_radius=18,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text("추천 알고리즘에 반영될 정보만 관리해요.", size=13, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            recommendation_category_row(),
                            *recommendation_rows(),
                        ],
                        spacing=0,
                    ),
                ),
                soft_button("FINDY 추천정보 저장", MAIN_COLOR, "white", save_recommendation, width=content_width()),
                ft.Container(height=24),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_beauty_profile_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "beauty_profile"
        beauty_categories = ["헤어", "네일아트", "메이크업", "포토", "웨딩", "반영구시술"]
        category_slug_map = {
            "헤어": "hair",
            "네일아트": "nail",
            "메이크업": "makeup",
            "포토": "photo",
            "웨딩": "wedding",
            "반영구시술": "semi_permanent",
        }

        default_profile = {
            "categories": ["메이크업", "헤어"],
            "skinType": "지성",
            "skinTraits": ["속건조", "여드름 피부"],
            "makeupConcerns": ["무너짐", "지속력"],
            "hairTraits": ["볼륨 부족"],
            "nailTraits": ["손톱 얇음", "유지력 약함"],
            "nailStyles": ["시럽", "프렌치"],
            "semiPermanentAreas": ["눈썹"],
            "semiPermanentConcerns": ["자연스러운 색", "빠른 탈각 걱정"],
            "photoPurposes": ["프로필", "SNS"],
            "photoMood": ["자연스러운", "고급스러운"],
            "weddingRoles": ["하객"],
            "weddingNeeds": ["오래 유지", "사진발"],
            "style": ["차가운", "귀여운"],
            "tone": "쿨톤",
            "preferredFinish": "세미매트",
            "avoidance": ["강한 향", "두꺼운 표현"],
            "budget": "상관없음",
            "visitPurpose": "데일리 관리",
            "memo": "지성인데 속건조가 있고, 오래 유지되는 메이크업을 선호해요.",
        }
        profile = app_state.setdefault("beauty_profile", default_profile)
        for key, value in default_profile.items():
            profile.setdefault(key, value.copy() if isinstance(value, list) else value)
        active_category = app_state.get("beauty_profile_active_category", "헤어")
        if active_category not in beauty_categories:
            active_category = "헤어"
            app_state["beauty_profile_active_category"] = active_category

        def scoped_key(field, category):
            return f"{field}_{category_slug_map.get(category, 'hair')}"

        def category_key(field, category=None):
            return scoped_key(field, category or active_category)

        category_defaults = {
            "헤어": {
                "style": ["내추럴", "고급스러운"],
                "avoidance": ["긴 시술 시간"],
                "budget": "중간",
                "visitPurpose": "데일리 관리",
                "memo": "볼륨과 손상도를 같이 고려한 헤어 콘텐츠를 선호해요.",
            },
            "네일아트": {
                "style": ["시럽", "프렌치"],
                "avoidance": ["파츠 과다"],
                "budget": "5~8만원",
                "visitPurpose": "데일리",
                "memo": "손톱이 얇아서 유지력과 손상 적은 제거를 중요하게 봐요.",
            },
            "메이크업": {
                "style": ["차가운", "귀여운"],
                "avoidance": ["두꺼운 표현", "과한 광"],
                "budget": "상관없음",
                "visitPurpose": "데일리",
                "memo": "지성인데 속건조가 있고 오래 유지되는 메이크업을 선호해요.",
            },
            "포토": {
                "style": ["자연스러운", "고급스러운"],
                "avoidance": ["과한 보정"],
                "budget": "10~20만원",
                "visitPurpose": "프로필",
                "memo": "자연스러운 표정과 얼굴형 보완이 잘 보이는 사진을 선호해요.",
            },
            "웨딩": {
                "style": ["자연스러운", "화사한"],
                "avoidance": ["너무 화려함"],
                "budget": "프리미엄",
                "visitPurpose": "촬영",
                "memo": "긴 일정에도 무너지지 않고 사진에서 깔끔하게 보이는 스타일을 원해요.",
            },
            "반영구시술": {
                "style": ["자연스러운", "또렷한"],
                "avoidance": ["진한 색"],
                "budget": "중간",
                "visitPurpose": "자연스러운 보완",
                "memo": "민낯에서도 어색하지 않은 자연스러운 결과를 선호해요.",
            },
        }
        for category, values in category_defaults.items():
            for field, value in values.items():
                profile.setdefault(category_key(field, category), value.copy() if isinstance(value, list) else value)

        def sync_beauty_to_user_profile():
            user_profile = get_user_profile()
            category_preferences = {}
            aggregated_styles = []
            for category in beauty_categories:
                category_styles = list(profile.get(category_key("style", category), []))
                for style in category_styles:
                    if style not in aggregated_styles:
                        aggregated_styles.append(style)
                category_preferences[category] = {
                    "style": category_styles,
                    "avoidance": list(profile.get(category_key("avoidance", category), [])),
                    "budget": profile.get(category_key("budget", category), ""),
                    "visitPurpose": profile.get(category_key("visitPurpose", category), ""),
                    "memo": profile.get(category_key("memo", category), ""),
                }
            user_profile["interestedFields"] = list(profile.get("categories", []))
            user_profile["styleKeywords"] = aggregated_styles or list(profile.get("style", []))
            user_profile["skinType"] = profile.get("skinType", "")
            user_profile["makeupConcern"] = ", ".join(profile.get("makeupConcerns", []))
            user_profile["hairConcern"] = ", ".join(profile.get("hairTraits", []))
            user_profile["personalTone"] = profile.get("tone", "")
            user_profile["budgetRange"] = profile.get(category_key("budget"), profile.get("budget", ""))
            user_profile["algorithmMemo"] = profile.get(category_key("memo"), profile.get("memo", ""))
            user_profile["beautyCategoryDetails"] = {
                "skinTraits": list(profile.get("skinTraits", [])),
                "makeupConcerns": list(profile.get("makeupConcerns", [])),
                "hairTraits": list(profile.get("hairTraits", [])),
                "nailTraits": list(profile.get("nailTraits", [])),
                "nailStyles": list(profile.get("nailStyles", [])),
                "semiPermanentAreas": list(profile.get("semiPermanentAreas", [])),
                "semiPermanentConcerns": list(profile.get("semiPermanentConcerns", [])),
                "photoPurposes": list(profile.get("photoPurposes", [])),
                "photoMood": list(profile.get("photoMood", [])),
                "weddingRoles": list(profile.get("weddingRoles", [])),
                "weddingNeeds": list(profile.get("weddingNeeds", [])),
                "categoryPreferences": category_preferences,
            }

        def profile_chip(value, key, multi=False):
            if multi:
                selected = value in profile.setdefault(key, [])
            else:
                selected = profile.get(key) == value

            def toggle(e):
                if multi:
                    values = profile.setdefault(key, [])
                    if value in values:
                        values.remove(value)
                    else:
                        values.append(value)
                else:
                    profile[key] = value
                sync_beauty_to_user_profile()
                show_beauty_profile_page()

            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=MAIN_COLOR if selected else "#FFFFFF",
                border_radius=18,
                border=ft.border.all(1, MAIN_COLOR if selected else BORDER_COLOR),
                on_click=toggle,
                ink=True,
                content=ft.Text(
                    value,
                    size=12,
                    color="#FFFFFF" if selected else TEXT_COLOR,
                    weight=ft.FontWeight.W_600,
                ),
            )

        def chip_section(title, subtitle, key, options, multi=False):
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=14, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
                        ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                        ft.Row(
                            controls=[profile_chip(option, key, multi=multi) for option in options],
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                        ),
                    ],
                    spacing=9,
                ),
            )

        def category_selector():
            def category_chip(category):
                active = active_category == category
                def choose(e):
                    app_state["beauty_profile_active_category"] = category
                    selected = profile.setdefault("categories", [])
                    if category not in selected:
                        selected.append(category)
                    sync_beauty_to_user_profile()
                    show_beauty_profile_page()
                return ft.Container(
                    padding=ft.padding.symmetric(horizontal=23, vertical=17),
                    bgcolor=MAIN_COLOR if active else "#FFFFFF",
                    border_radius=28,
                    border=ft.border.all(1.3, MAIN_COLOR if active else BORDER_COLOR),
                    on_click=choose,
                    ink=True,
                    content=ft.Text(
                        category,
                        size=15,
                        color="#FFFFFF" if active else TEXT_COLOR,
                        weight=ft.FontWeight.W_900,
                    ),
                )
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=20, vertical=20),
                bgcolor="#FFFFFF",
                border_radius=RADIUS_XL,
                border=ft.border.all(1.2, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text("카테고리", size=21, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ft.Text("FINDY2에서 수집할 핵심 뷰티 분야예요.", size=13, color=SUBTEXT_COLOR),
                        ft.Row(
                            controls=[category_chip(category) for category in beauty_categories],
                            wrap=True,
                            spacing=12,
                            run_spacing=12,
                        ),
                    ],
                    spacing=16,
                ),
            )

        style_options_by_category = {
            "헤어": ["내추럴", "차분한", "힙한", "고급스러운", "러블리", "시크한", "청순한", "화려한"],
            "네일아트": ["깔끔한", "시럽", "프렌치", "글리터", "귀여운", "화려한", "오피스", "웨딩"],
            "메이크업": ["차가운", "귀여운", "도도한", "내추럴", "화려한", "청순한", "힙한", "고급스러운"],
            "포토": ["자연스러운", "고급스러운", "청량한", "시크한", "따뜻한", "필름감성", "화보느낌", "보정 적게"],
            "웨딩": ["자연스러운", "화사한", "우아한", "고급스러운", "깔끔한", "러블리", "클래식", "화려한"],
            "반영구시술": ["자연스러운", "또렷한", "깔끔한", "부드러운", "대칭감", "민낯 친화", "선명한", "은은한"],
        }
        budget_options_by_category = {
            "헤어": ["상관없음", "5만원 이하", "5~10만원", "10~20만원", "20만원 이상", "가성비", "프리미엄"],
            "네일아트": ["상관없음", "3만원 이하", "3~5만원", "5~8만원", "8만원 이상", "가성비", "프리미엄"],
            "메이크업": ["상관없음", "5만원 이하", "5~10만원", "10~20만원", "20만원 이상", "가성비", "프리미엄"],
            "포토": ["상관없음", "10만원 이하", "10~20만원", "20~40만원", "40만원 이상", "가성비", "프리미엄"],
            "웨딩": ["상관없음", "20만원 이하", "20~50만원", "50~100만원", "100만원 이상", "가성비", "프리미엄"],
            "반영구시술": ["상관없음", "10만원 이하", "10~20만원", "20~40만원", "40만원 이상", "가성비", "프리미엄"],
        }
        purpose_options_by_category = {
            "헤어": ["데일리 관리", "기분전환", "촬영", "데이트", "면접", "웨딩", "여행"],
            "네일아트": ["데일리", "기분전환", "여행", "촬영", "웨딩", "계절 아트", "손톱 관리"],
            "메이크업": ["데일리", "데이트", "면접", "촬영", "하객", "파티", "피부 보완"],
            "포토": ["프로필", "증명사진", "SNS", "커플", "우정", "가족", "브랜드/제품", "웨딩 스냅"],
            "웨딩": ["본식", "촬영", "하객", "혼주", "드레스투어", "브라이덜샤워", "스몰웨딩"],
            "반영구시술": ["자연스러운 보완", "민낯 관리", "대칭 보완", "선명도 보완", "유지력 개선", "리터치"],
        }
        avoidance_options_by_category = {
            "헤어": ["긴 시술 시간", "두피 자극", "강한 향", "손상 우려", "과한 볼륨", "너무 밝은 색"],
            "네일아트": ["파츠 과다", "너무 긴 길이", "손상 우려", "강한 컬러", "두꺼운 젤", "긴 시술 시간"],
            "메이크업": ["강한 향", "두꺼운 표현", "자극감", "과한 광", "과한 음영", "마스크 묻어남"],
            "포토": ["과한 보정", "어두운 분위기", "강한 콘트라스트", "부자연스러운 포즈", "긴 촬영 시간", "노출 많은 콘셉트"],
            "웨딩": ["너무 화려함", "무거운 헤어", "두꺼운 베이스", "눈물 번짐", "긴 대기 시간", "과한 장식"],
            "반영구시술": ["진한 색", "부자연스러운 라인", "통증 걱정", "붓기 걱정", "긴 회복 기간", "색 빠짐"],
        }

        def category_memo_section():
            key = category_key("memo")
            memo_field = ft.TextField(
                width=content_width(),
                value=profile.get(key, ""),
                multiline=True,
                min_lines=4,
                max_lines=6,
                hint_text=f"{active_category}에서 원하는 스타일, 고민, 참고사항을 적어주세요.",
                border_radius=16,
                bgcolor="#FFFFFF",
                border_color=BORDER_COLOR,
                focused_border_color=MAIN_COLOR,
                cursor_color=MAIN_COLOR,
                content_padding=16,
                on_change=lambda e: (profile.__setitem__(key, e.control.value or ""), sync_beauty_to_user_profile()),
            )
            return ft.Container(
                width=content_width(),
                padding=SPACE_LG,
                bgcolor="#FFFFFF",
                border_radius=RADIUS_LG,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text("메모", size=14, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
                        ft.Text(f"{active_category}만의 취향과 고민을 따로 저장해요.", size=11, color=SUBTEXT_COLOR),
                        memo_field,
                    ],
                    spacing=9,
                ),
            )

        def category_preference_sections():
            return [
                chip_section("선호 스타일", f"{active_category}에서 원하는 분위기를 선택해요.", category_key("style"), style_options_by_category.get(active_category, []), multi=True),
                chip_section("방문 목적", f"{active_category} 추천 상황을 골라요.", category_key("visitPurpose"), purpose_options_by_category.get(active_category, [])),
                chip_section("예산", f"{active_category} 가격대 추천을 위한 값이에요.", category_key("budget"), budget_options_by_category.get(active_category, [])),
                chip_section("피하고 싶은 요소", f"{active_category} 추천에서 제외하거나 낮게 볼 요소예요.", category_key("avoidance"), avoidance_options_by_category.get(active_category, []), multi=True),
                category_memo_section(),
            ]

        def selected_category_sections():
            sections_by_category = {
                "헤어": [
                    chip_section("헤어 특징", "헤어 콘텐츠 추천에 활용해요.", "hairTraits", ["볼륨 부족", "손상모", "곱슬", "탈색모", "두피 민감", "숱 많음", "숱 적음", "유분 많은 두피"], multi=True),
                ],
                "네일아트": [
                    chip_section("네일아트 특징", "네일 유지력과 손톱 컨디션 추천에 활용해요.", "nailTraits", ["손톱 얇음", "잘 부러짐", "갈라짐", "벗겨짐", "세로줄", "큐티클 건조", "짧은 손톱", "유지력 약함", "파츠 잘 떨어짐"], multi=True),
                    chip_section("네일 선호", "디자인과 시술 방식 추천에 반영돼요.", "nailStyles", ["시럽", "프렌치", "그라데이션", "풀컬러", "글리터", "파츠", "짧은 손톱 아트", "오피스", "웨딩 네일", "손상 적은 제거"], multi=True),
                ],
                "메이크업": [
                    chip_section("피부 타입", "기본 피부 타입을 하나 선택해요.", "skinType", ["지성", "건성", "복합성", "민감성", "보통", "수부지"]),
                    chip_section("나의 특징", "추천 필터에 강하게 반영할 피부/컨디션 특징이에요.", "skinTraits", ["속건조", "여드름 피부", "홍조", "넓은 모공", "피지 많음", "각질", "색소침착", "탄력 저하", "알레르기 민감"], multi=True),
                    chip_section("메이크업 고민", "메이크업 추천과 리뷰 필터에 활용해요.", "makeupConcerns", ["무너짐", "다크닝", "요철", "커버력", "지속력", "유분", "건조 끼임", "마스크 묻어남"], multi=True),
                    chip_section("퍼스널 톤", "모르면 잘 모름으로 두어도 괜찮아요.", "tone", ["웜톤", "쿨톤", "뉴트럴", "잘 모름"]),
                    chip_section("선호 표현", "메이크업 스타일 추천에 반영돼요.", "preferredFinish", ["매트", "세미매트", "글로우", "물광", "보송", "또렷한 윤곽"]),
                ],
                "포토": [
                    chip_section("포토 목적", "스냅/촬영 콘텐츠 추천에 활용해요.", "photoPurposes", ["프로필", "증명사진", "SNS", "바디프로필", "커플", "우정", "가족", "브랜드/제품", "웨딩 스냅"], multi=True),
                    chip_section("포토 무드", "사진 스타일과 작가/스냅 추천 기준이에요.", "photoMood", ["자연스러운", "고급스러운", "청량한", "시크한", "따뜻한", "필름감성", "화보느낌", "보정 적게", "얼굴형 보완"], multi=True),
                ],
                "웨딩": [
                    chip_section("웨딩 역할", "웨딩 관련 추천을 세분화해요.", "weddingRoles", ["신부", "신랑", "혼주", "하객", "브라이덜샤워", "본식 전 촬영", "스몰웨딩"], multi=True),
                    chip_section("웨딩 니즈", "긴 일정과 사진 결과를 고려한 선호예요.", "weddingNeeds", ["오래 유지", "사진발", "눈물/땀 걱정", "자연스러운", "화려한", "글로우 피부", "업스타일", "잔머리 정리", "피부관리 포함"], multi=True),
                ],
                "반영구시술": [
                    chip_section("반영구시술 부위", "관심 있는 반영구 영역을 선택해요.", "semiPermanentAreas", ["눈썹", "아이라인", "입술", "헤어라인", "두피 SMP", "점/주근깨 커버"], multi=True),
                    chip_section("반영구 고민", "유지력과 회복/색상 선호를 추천에 반영해요.", "semiPermanentConcerns", ["자연스러운 색", "또렷한 라인", "빠른 탈각 걱정", "붓기 걱정", "통증 걱정", "색 빠짐", "유분 많은 피부", "민감 피부", "리터치 필요"], multi=True),
                    chip_section("피부 타입", "반영구시술 유지력 참고용으로 저장해요.", "skinType", ["지성", "건성", "복합성", "민감성", "보통", "수부지"]),
                ],
            }
            return sections_by_category.get(active_category, []) + category_preference_sections()

        def save_beauty_profile(e=None):
            sync_beauty_to_user_profile()
            if not sync_profile_to_auth(get_user_profile()):
                return
            persist_user_data(notify_on_error=True)
            show_snack("나의 FINDY가 추천 기준에 반영되었어요.")

        body = ft.Column(
            controls=[
                page_header("나의 FINDY", on_back=go_back_page),
                ft.Text("카테고리별 특징, 스타일, 예산, 목적, 메모를 따로 저장해 FINDY2 추천 데이터로 쌓아둘게요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=16, vertical=14),
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=RADIUS_LG,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.34, MAIN_COLOR)),
                    content=ft.Column(
                        controls=[
                            ft.Text("추천 알고리즘용 핵심 데이터", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                            ft.Text("피부 타입은 건성·지성·복합성·민감성 같은 기본 타입과, 여드름/속건조 같은 특징을 따로 저장해요.", size=11, color=SUBTEXT_COLOR),
                        ],
                        spacing=5,
                    ),
                ),
                category_selector(),
                ft.Container(
                    width=content_width(),
                    content=ft.Text(f"{active_category} 맞춤 항목", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                ),
                *selected_category_sections(),
                soft_button("나의 FINDY 저장", MAIN_COLOR, "white", save_beauty_profile),
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
            ("예약 기능은 언제 사용할 수 있나요?", "FINDY2에서는 커뮤니티 데이터를 먼저 모으고, 추후 FINDY 본서비스에서 예약 기능을 연결할 예정이에요."),
            ("문의는 얼마나 빨리 답변되나요?", "운영시간 기준 순차적으로 확인하며 보통 1영업일 안에 답변드려요."),
            ("앱 정보가 실제와 다른가요?", "문의내역으로 알려주시면 확인 후 빠르게 반영할게요."),
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
        categories = ["예약/결제", "서비스 오류", "서비스 제안", "기타"]

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
        last_message = messages[-1] if messages else {"text": "아직 소식이 없어요.", "time": ""}
        title = (thread.get("room_name") or thread.get("artist_name") or "FINDY 소식") if mode == "customer" else thread.get("customer_name", "고객")
        meta = f'{thread.get("category", "소식")} · {thread.get("updated_at", "")}'
        status = thread.get("status", "안내")

        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor="#FFFFFF",
            border_radius=RADIUS_XL,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=lambda e, thread_id=thread.get("id"): open_message_thread(
                thread_id,
                "customer_messages",
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

    def message_video_tip_card(video):
        return ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=14, vertical=13),
            bgcolor="#FFFFFF",
            border_radius=RADIUS_LG,
            border=ft.border.all(1, BORDER_COLOR),
            on_click=lambda e, item=video: show_video_detail_page(item),
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=64,
                        height=82,
                        border_radius=18,
                        bgcolor="#000000",
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Stack(
                            controls=[
                                black_image_box(64, 82),
                                ft.Container(
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(app_icon("PLAY_CIRCLE", "PLAY_CIRCLE_FILLED"), size=30, color=MAIN_COLOR),
                                ),
                            ],
                        ),
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                        bgcolor=CHIP_BG,
                                        border_radius=999,
                                        content=ft.Text(video.get("category", "팁"), size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_700),
                                    ),
                                    ft.Text(video.get("duration", "0:59"), size=10, color=SUBTEXT_COLOR),
                                ],
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(video.get("title", "비디오 팁"), size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800, max_lines=1),
                            ft.Text(video.get("subtitle", "FINDY 회원의 뷰티 팁"), size=11, color=SUBTEXT_COLOR, max_lines=2),
                            ft.Text(f'조회 {video.get("views", "0")} · 저장 가능', size=10, color=SUBTEXT_COLOR),
                        ],
                        spacing=5,
                        expand=True,
                    ),
                    ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=18, color=SUBTEXT_COLOR),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def message_video_gateway_card():
        recent_videos = get_all_video_items()[:2]
        return ft.Container(
            width=content_width(),
            padding=SPACE_LG,
            bgcolor=MAIN_COLOR_SOFT,
            border_radius=RADIUS_XL,
            border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=46,
                                height=46,
                                border_radius=16,
                                bgcolor="#FFFFFF",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(app_icon("SMART_DISPLAY_OUTLINED", "PLAY_CIRCLE"), color=MAIN_COLOR, size=24),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("비디오 팁 소식", size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                                    ft.Text("본인만의 뷰티 팁을 짧은 영상으로 공유해요.", size=12, color=SUBTEXT_COLOR),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            soft_button("팁 올리기", MAIN_COLOR, "white", lambda e: show_write_video_page(), width=int((content_width() - 50) / 2)),
                            soft_button("비디오 보기", "#FFFFFF", MAIN_COLOR_DARK, lambda e: show_video_page(), border=ft.border.all(1, BORDER_COLOR), width=int((content_width() - 50) / 2)),
                        ],
                        spacing=10,
                    ),
                    *[message_video_tip_card(video) for video in recent_videos],
                ],
                spacing=12,
            ),
        )

    def show_customer_messages_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 2
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
                            ft.Text("아직 소식이 없어요.", size=16, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                            ft.Text("FINDY 안내와 커뮤니티 활동 알림이 이곳에 정리돼요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            ]

        body = ft.Column(
            controls=[
                message_header("소식함", on_back=go_back_page),
                ft.Text("FINDY 안내, 비디오 팁, 커뮤니티 활동 알림을 한 곳에서 확인해요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
                message_video_gateway_card(),
                section_title("FINDY 소식", "팁 공유와 커뮤니티 활동 알림을 확인해요."),
                *cards,
                ft.Container(height=24),
            ],
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        make_shell(body, app_state["selected_tab"])

    def show_message_detail_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 2
        app_state["current_page"] = "message_detail"
        thread = find_message_thread(app_state.get("active_message_thread_id"))
        if not thread:
            show_customer_messages_page()
            return

        def go_message_back(e=None):
            target = app_state.get("message_back_target")
            if target == "detail":
                show_detail_page()
            elif target == "search_results":
                show_search_results_page()
            else:
                show_customer_messages_page()

        def message_bubble(message):
            own = message.get("sender") == "customer"
            sender_label = "FINDY" if message.get("sender") == "system" else thread.get("customer_name", "나")
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
            hint_text="답장을 입력해주세요.",
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
                show_snack("답장 내용을 입력해주세요.", bgcolor="#B85C5C")
                return
            append_thread_message(thread, "customer", text)
            snack_text = "답장이 남겨졌어요."
            app_state["message_reply_draft"] = ""
            show_snack(snack_text)
            show_message_detail_page()

        reply_controls = (
            [
                ft.Text("답장", size=13, weight=ft.FontWeight.W_800, color=TEXT_COLOR),
                reply_field,
                soft_button("답장 남기기", MAIN_COLOR, "white", send_reply, width=content_width() - 32),
            ]
            if FINDY2_DIRECT_MESSAGE_ENABLED
            else [
                ft.Text("답장 기능은 준비 중이에요.", size=14, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
                ft.Text("FINDY2에서는 소식 확인만 제공하고, 직접 대화 기능은 추후 업데이트에서 연결할 예정이에요.", size=12, color=SUBTEXT_COLOR),
            ]
        )

        body = ft.Column(
            controls=[
                page_header("소식 상세", on_back=go_message_back),
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
                                                thread.get("room_name", thread.get("artist_name", "FINDY 소식")),
                                                size=18,
                                                color=TEXT_COLOR,
                                                weight=ft.FontWeight.W_800,
                                            ),
                                            ft.Text(f'{thread.get("category", "소식")} · {thread.get("status", "안내")}', size=12, color=SUBTEXT_COLOR),
                                        ],
                                        spacing=4,
                                        expand=True,
                                    ),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        bgcolor=CHIP_BG,
                                        border_radius=999,
                                        content=ft.Text("커뮤니티 소식", size=10, color=MAIN_COLOR, weight=ft.FontWeight.W_700),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text("비디오 팁과 커뮤니티 활동을 한 곳에서 이어서 관리해요.", size=11, color=SUBTEXT_COLOR),
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
                        controls=reply_controls,
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
        app_state["selected_tab"] = 2
        app_state["current_page"] = "notifications"
        app_state["notification_read_at"] = datetime.now()
        items = current_notification_items()
        intro_text = "커뮤니티 활동, 리뷰, 나의 FINDY 관련 알림을 모아봤어요."

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

        async def transition_to_home_beauty_category(category_name, display_label=None):
            label = display_label or category_name
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
                                ft.Text(label, size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ft.Text(f"{label} 전용 페이지로 이동 중이에요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
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
            app_state["selected_beauty_category"] = category_name
            app_state["selected_tab"] = 2
            show_beauty_category_page(category_name)

        def go_to_home_beauty_category(category_name, display_label=None):
            def handler(e):
                page.run_task(transition_to_home_beauty_category, category_name, display_label)
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
                ]
            ),
        )

        home_search_submit = submit_global_search
        home_search_hint = "궁금한 시술, 리뷰, 질문을 검색해보세요"

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
                            category_square("CUT", "헤어", go_to_home_beauty_category("헤어")),
                            category_square("BRUSH", "네일아트", go_to_home_beauty_category("네일아트")),
                            category_square("FACE", "메이크업", go_to_home_beauty_category("메이크업")),
                        ],
                        spacing=slim_gap,
                    ),
                    ft.Row(
                        controls=[
                            category_square("CAMERA_ALT", "포토", go_to_home_beauty_category("포토")),
                            category_square("FAVORITE", "웨딩", go_to_home_beauty_category("웨딩")),
                            category_square("AUTO_FIX_HIGH", "반영구시술", go_to_home_beauty_category("반영구시술", "반영구시술")),
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

        hero_controls = []
        if upcoming_card:
            hero_controls.extend([
                upcoming_card,
                ft.Container(height=12),
            ])
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

        def home_community_preview_card(post, board_type="전체"):
            def open_post(e=None):
                app_state["selected_tab"] = 0
                app_state["content_detail_back_page"] = "home"
                open_content_detail(post, back_page="home")

            badge = post.get("post_type", post.get("badge", board_type if board_type != "전체" else "인기"))
            return ft.Container(
                width=270,
                height=116,
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                bgcolor="#FFFFFF",
                border_radius=22,
                border=ft.border.all(1, ft.Colors.with_opacity(0.78, BORDER_COLOR)),
                on_click=open_post,
                ink=True,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color="#08000000",
                    offset=ft.Offset(0, 4),
                ),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(post.get("title", "게시글"), size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, expand=True, max_lines=1),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=9, vertical=3),
                                    bgcolor=ft.Colors.with_opacity(0.66, CHIP_BG),
                                    border_radius=999,
                                    border=ft.border.all(1, ft.Colors.with_opacity(0.55, BORDER_COLOR)),
                                    content=ft.Text(badge, size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Text(post.get("subtitle", post.get("category", "커뮤니티")), size=11, color=SUBTEXT_COLOR, max_lines=1),
                        ft.Container(
                            padding=ft.padding.only(top=4, left=2),
                            content=ft.Text(post.get("meta", "댓글 0 · 저장 0"), size=11, color=SUBTEXT_COLOR, max_lines=1),
                        ),
                    ],
                    spacing=6,
                ),
            )

        def build_home_community_preview(board_type="전체", limit=3):
            posts = filtered_community_posts(board_type, "전체")[:limit]
            if not posts:
                return ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("아직 게시글이 없어요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            return ft.Container(
                width=content_width(),
                height=128,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    controls=[home_community_preview_card(post, board_type) for post in posts],
                    spacing=10,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )

        def home_snap_preview_card(item):
            def open_snap(e=None):
                app_state["snap_detail_item"] = item
                app_state["snap_filter"] = item.get("category", "전체")
                app_state["current_page"] = "snap_detail"
                show_snap_detail_page()

            return ft.Container(
                width=108,
                on_click=open_snap,
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
                                    black_image_box(108, 132),
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
                        ft.Text(item.get("title", "스냅"), size=12, color=TEXT_COLOR, weight=ft.FontWeight.BOLD, max_lines=1),
                    ],
                    spacing=7,
                ),
            )

        def build_home_snap_preview():
            snaps = []
            for category_name in ["헤어", "네일아트", "메이크업", "웨딩", "포토", "반영구"]:
                snaps.extend(get_snap_feed_items("recommended", category_name)[:1])
            if not snaps:
                return ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("아직 FINDY 스냅이 없어요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            return ft.Container(
                width=content_width(),
                height=174,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    controls=[home_snap_preview_card(item) for item in snaps[:6]],
                    spacing=8,
                    scroll=ft.ScrollMode.HIDDEN,
                ),
            )

        def home_video_preview_card(video):
            return ft.Container(
                width=270,
                height=150,
                padding=ft.padding.symmetric(horizontal=14, vertical=13),
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, BORDER_COLOR),
                on_click=lambda e, item=video: show_video_detail_page(item),
                ink=True,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=14,
                    color="#0A000000",
                    offset=ft.Offset(0, 5),
                ),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=78,
                            height=118,
                            border_radius=16,
                            bgcolor="#000000",
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=ft.Stack(
                                controls=[
                                    black_image_box(78, 118),
                                    ft.Container(
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(app_icon("PLAY_CIRCLE", "PLAY_CIRCLE_FILLED"), size=34, color=MAIN_COLOR),
                                    ),
                                    ft.Container(
                                        left=8,
                                        bottom=8,
                                        padding=ft.padding.symmetric(horizontal=7, vertical=3),
                                        bgcolor=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                                        border_radius=999,
                                        content=ft.Text(video.get("duration", "0:59"), size=8, color=TEXT_COLOR, weight=ft.FontWeight.W_700),
                                    ),
                                ],
                            ),
                        ),
                        ft.Column(
                            controls=[
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=CHIP_BG,
                                    border_radius=999,
                                    content=ft.Text(video.get("category", "비디오"), size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_600),
                                ),
                                ft.Text(video.get("title", "비디오"), size=14, color=TEXT_COLOR, weight=ft.FontWeight.BOLD, max_lines=2),
                                ft.Text(video.get("subtitle", ""), size=11, color=SUBTEXT_COLOR, max_lines=2),
                                ft.Text(f'조회 {video.get("views", "0")}', size=10, color=SUBTEXT_COLOR, max_lines=1),
                            ],
                            spacing=7,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def build_home_video_preview(limit=3):
            videos = get_all_video_items()[:limit]
            if not videos:
                return ft.Container(
                    width=content_width(),
                    padding=SPACE_LG,
                    bgcolor="#FFFFFF",
                    border_radius=RADIUS_XL,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Text("아직 FINDY 비디오가 없어요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                )
            return ft.Container(
                width=content_width(),
                height=162,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    controls=[home_video_preview_card(video) for video in videos],
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

        popular_block = animated_block(
            ft.Column(
                controls=[
                    section_title("인기글", "지금 많이 보는 글", on_click=lambda e: show_community_board_page("인기", selected_tab=0)),
                    build_home_community_preview("인기", 3),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        review_block = animated_block(
            ft.Column(
                controls=[
                    section_title("리뷰", "방문 후기", on_click=lambda e: show_review_page()),
                    build_home_review_preview(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        question_block = animated_block(
            ft.Column(
                controls=[
                    section_title("질문", "답변이 필요한 질문", on_click=lambda e: show_community_board_page("질문", selected_tab=0)),
                    build_home_community_preview("질문", 2),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        free_board_block = animated_block(
            ft.Column(
                controls=[
                    section_title("자유게시판", "자유로운 이야기", on_click=lambda e: show_community_board_page("자유", selected_tab=0)),
                    build_home_community_preview("자유", 2),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        findy_snap_block = animated_block(
            ft.Column(
                controls=[
                    section_title("FINDY 스냅", "사진으로 보기", on_click=lambda e: show_snap_page()),
                    build_home_snap_preview(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        findy_video_block = animated_block(
            ft.Column(
                controls=[
                    section_title("FINDY 비디오", "짧은 팁 영상", on_click=lambda e: show_video_page()),
                    build_home_video_preview(),
                ],
                spacing=SPACE_MD,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        animated_sections = [hero_block, popular_block, review_block, question_block, free_board_block, findy_snap_block, findy_video_block]

        body_controls = [
            hero_block,
            ft.Container(height=16),
            popular_block,
            ft.Container(height=18),
            review_block,
            ft.Container(height=18),
            question_block,
            ft.Container(height=18),
            free_board_block,
            ft.Container(height=18),
            findy_snap_block,
            ft.Container(height=18),
            findy_video_block,
            ft.Container(height=18),
        ]

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

    def get_snap_feed_items(sort_mode, category_filter="전체"):
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

        normalized_filter = normalize_content_filter(category_filter)
        items = [
            item.copy()
            for item in base_items
            if normalized_filter == "전체" or normalize_overlay_category_name(item["category"]) == normalized_filter
        ]
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
            width=27,
            height=27,
            bgcolor=CARD_COLOR if active else ft.Colors.TRANSPARENT,
            border_radius=9,
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
        active = app_state.get("snap_filter", "전체") == label

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
            selected_artist_text.value = current.get("artist_name") or current.get("displayName") or current.get("creatorName", "FINDY 회원")
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
                    ft.Text("방문/이용 기록", size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
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
        image_path = item.get("image_path") or ((item.get("photos") or [None])[0])
        media_control = (
            ft.Image(src=image_path, width=width, height=height, fit=ft.ImageFit.COVER)
            if image_path
            else black_image_box(width, height)
        )
        tile = ft.Container(
            width=width,
            height=height,
            border_radius=4,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            content=ft.Stack(
                controls=[
                    media_control,
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
        title_label = ft.Container(
            height=28,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(title, size=24, weight=ft.FontWeight.W_900, color=TEXT_COLOR),
        )
        return ft.Container(
            width=content_width(),
            content=ft.Stack(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Column(
                                controls=[
                                    title_label,
                                    ft.Text(subtitle, size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
                                ],
                                spacing=4,
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

        snap_sort_labels = [("인기순", "popular"), ("최신순", "latest"), ("추천순", "recommended")]
        snap_category_labels = ["전체", "헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
        snap_sort_label_map = {key: label for label, key in snap_sort_labels}

        def choose_snap_sort(key):
            def handler(e):
                app_state["snap_sort_mode"] = key
                app_state["snap_filter_drawer"] = None
                show_snap_page()
            return handler

        def choose_snap_category(label):
            def handler(e):
                app_state["snap_filter"] = label
                app_state["snap_filter_drawer"] = None
                show_snap_page()
            return handler

        def toggle_snap_drawer(kind):
            def handler(e):
                current = app_state.get("snap_filter_drawer")
                app_state["snap_filter_drawer"] = None if current == kind else kind
                show_snap_page()
            return handler

        def snap_drawer_option(label, active, on_click):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=13, vertical=8),
                bgcolor=MAIN_COLOR if active else CARD_COLOR,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR),
                on_click=on_click,
                ink=True,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                content=ft.Text(
                    label,
                    size=11,
                    color="#FFFFFF" if active else TEXT_COLOR,
                    weight=ft.FontWeight.W_900 if active else ft.FontWeight.W_700,
                ),
            )

        def snap_drawer_button(label, value, kind):
            opened = app_state.get("snap_filter_drawer") == kind
            return ft.Container(
                width=88 if kind == "category" else 100,
                height=38,
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                bgcolor=CHIP_BG if opened else CARD_COLOR,
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if opened else BORDER_COLOR),
                on_click=toggle_snap_drawer(kind),
                ink=True,
                animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                content=ft.Row(
                    controls=[
                        ft.Text(label, size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                        ft.Text(value, size=11, color=MAIN_COLOR_DARK if opened else TEXT_COLOR, weight=ft.FontWeight.W_900, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Icon(app_icon("KEYBOARD_ARROW_UP" if opened else "KEYBOARD_ARROW_DOWN", "EXPAND_MORE"), size=14, color=MAIN_COLOR_DARK if opened else SUBTEXT_COLOR),
                    ],
                    spacing=3,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
            )

        def snap_drawer_panel():
            drawer = app_state.get("snap_filter_drawer")
            if drawer == "sort":
                controls = [
                    snap_drawer_option(label, app_state.get("snap_sort_mode", "popular") == key, choose_snap_sort(key))
                    for label, key in snap_sort_labels
                ]
            elif drawer == "category":
                controls = [
                    snap_drawer_option(label, app_state.get("snap_filter", "전체") == label, choose_snap_category(label))
                    for label in snap_category_labels
                ]
            else:
                return None
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=ft.Colors.with_opacity(0.58, CHIP_BG),
                border_radius=22,
                border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                content=ft.Row(
                    controls=controls,
                    spacing=7,
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        layout_toggle = ft.Container(
            width=61,
            height=38,
            padding=ft.padding.all(2),
            bgcolor=CHIP_BG,
            border_radius=12,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Row(
                controls=[
                    snap_layout_selector_button(1, app_state.get("snap_layout_mode", 3), choose_layout(1)),
                    snap_layout_selector_button(3, app_state.get("snap_layout_mode", 3), choose_layout(3)),
                ],
                spacing=2,
            ),
        )

        selector_row = ft.Container(
            width=content_width(),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=86,
                        height=38,
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        bgcolor=MAIN_COLOR_SOFT,
                        border_radius=999,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.35, MAIN_COLOR)),
                        on_click=lambda e: (app_state.__setitem__("current_page", "write_snap"), show_write_snap_page()),
                        ink=True,
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, size=16, color=MAIN_COLOR),
                                ft.Text("스냅작성", size=10, color=MAIN_COLOR, weight=ft.FontWeight.W_900, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            tight=True,
                        ),
                    ),
                    ft.Row(
                        controls=[
                            snap_drawer_button("분야", app_state.get("snap_filter", "전체"), "category"),
                            snap_drawer_button("정렬", snap_sort_label_map.get(app_state.get("snap_sort_mode", "popular"), "인기순"), "sort"),
                        ],
                        spacing=6,
                    ),
                    layout_toggle,
                ],
                spacing=6,
                scroll=ft.ScrollMode.HIDDEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        drawer_panel = snap_drawer_panel()

        body = ft.Column(
            controls=[
                selector_row,
                ft.Container(height=8),
                *([drawer_panel] if drawer_panel else []),
                ft.Container(height=10),
                build_snap_feed(
                    app_state.get("snap_layout_mode", 3),
                    app_state.get("snap_sort_mode", "popular"),
                    app_state.get("snap_filter", "전체"),
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

        selected_category = [app_state.get("snap_filter", "전체")]
        if selected_category[0] == "전체":
            selected_category[0] = "헤어"
        snap_category_row = ft.Row(spacing=6, scroll=ft.ScrollMode.HIDDEN)
        category_controls = []

        def refresh_snap_write_categories():
            for control, category in category_controls:
                active = selected_category[0] == category
                control.bgcolor = MAIN_COLOR if active else CHIP_BG
                control.border = ft.border.all(1, MAIN_COLOR if active else BORDER_COLOR)
                control.content.color = "#FFFFFF" if active else TEXT_COLOR

        def choose_snap_write_category(category):
            def handler(e):
                selected_category[0] = category
                refresh_snap_write_categories()
                page.update()
            return handler

        for category in ["헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]:
            chip_control = ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                border_radius=999,
                on_click=choose_snap_write_category(category),
                ink=True,
                content=ft.Text(category, size=12, weight=ft.FontWeight.W_700),
            )
            category_controls.append((chip_control, category))
            snap_category_row.controls.append(chip_control)
        refresh_snap_write_categories()

        title_field = compose_text_field("예: 브라이드 무드 스냅", size=20, weight=ft.FontWeight.W_900)
        note_field = compose_text_field(
            "사진 분위기나 시술 포인트를 짧게 남겨주세요.\n#무드 #컬러 #스타일...",
            multiline=True,
            min_lines=8,
            max_lines=12,
            size=14,
        )
        selected_photos = []
        snap_photo_row = ft.Row(spacing=8, scroll=ft.ScrollMode.HIDDEN)
        snap_photo_preview = ft.Container(width=content_width() - 36, visible=False, content=snap_photo_row)
        snap_photo_count = ft.Text("0/10", size=10, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700)

        def refresh_snap_photo_preview():
            snap_photo_row.controls.clear()
            for index, path in enumerate(selected_photos):
                def remove_photo(e=None, target_index=index):
                    selected_photos.pop(target_index)
                    refresh_snap_photo_preview()

                snap_photo_row.controls.append(
                    ft.Stack(
                        width=82,
                        height=102,
                        controls=[
                            ft.Image(src=path, width=82, height=102, fit=ft.ImageFit.COVER, border_radius=12),
                            ft.Container(
                                right=4,
                                top=4,
                                width=22,
                                height=22,
                                border_radius=11,
                                bgcolor=ft.Colors.with_opacity(0.72, "#000000"),
                                alignment=ft.Alignment(0, 0),
                                on_click=remove_photo,
                                ink=True,
                                content=ft.Icon(app_icon("CLOSE"), size=13, color="#FFFFFF"),
                            ),
                        ],
                    )
                )
            snap_photo_preview.visible = bool(selected_photos)
            snap_photo_count.value = f"{len(selected_photos)}/10"
            page.update()

        def on_snap_photos_picked(e: ft.FilePickerResultEvent):
            if not e.files:
                return
            remaining = 10 - len(selected_photos)
            for selected_file in e.files[:remaining]:
                if not selected_file.path:
                    continue
                try:
                    validate_image_file(selected_file.path)
                except MediaStorageError as error:
                    show_snack(str(error), bgcolor="#B85C5C")
                    continue
                if selected_file.path not in selected_photos:
                    selected_photos.append(selected_file.path)
            refresh_snap_photo_preview()
            if len(e.files) > remaining:
                show_snack("스냅 사진은 최대 10장까지 등록할 수 있어요.", bgcolor="#B85C5C")

        snap_photo_picker = ft.FilePicker(on_result=on_snap_photos_picked)
        page.overlay.append(snap_photo_picker)
        page.update()

        def pick_snap_photos(e=None):
            if len(selected_photos) >= 10:
                show_snack("스냅 사진은 최대 10장까지 등록할 수 있어요.", bgcolor="#B85C5C")
                return
            snap_photo_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "gif"],
            )

        def go_back_from_snap_write(e=None):
            if snap_photo_picker in page.overlay:
                page.overlay.remove(snap_photo_picker)
            show_snap_page()

        def submit_snap(e):
            title = (title_field.value or "").strip()
            note = (note_field.value or "").strip()
            if not title:
                show_snack("스냅 제목을 입력해주세요.", bgcolor="#B85C5C")
                return
            if not selected_photos:
                show_snack("스냅 사진을 한 장 이상 선택해주세요.", bgcolor="#B85C5C")
                return
            try:
                stored_images = store_images(
                    selected_photos,
                    FINDY2_MEDIA_DIR,
                    current_user_id(),
                    limit=10,
                )
            except MediaStorageError as error:
                show_snack(str(error), bgcolor="#B85C5C")
                return
            snap = {
                "id": f"user_{len(app_state.get('written_snaps', [])) + 1}",
                "userId": current_user_id(),
                "category": selected_category[0],
                "title": title,
                "artist_id": None,
                "artist_name": "",
                "service": selected_category[0],
                "description": note,
                "emoji": "📷",
                "likes": 0,
                "saves": 0,
                "views": 0,
                "ts": 999 + len(app_state.get("written_snaps", [])),
                "image_path": stored_images[0]["path"],
                "photos": [item["path"] for item in stored_images],
                "imageMetadata": stored_images,
            }
            app_state.setdefault("written_snaps", []).insert(0, snap)
            app_state["snap_filter"] = snap["category"]
            if not persist_user_data(notify_on_error=True):
                app_state["written_snaps"].remove(snap)
                for stored_image in stored_images:
                    remove_media_file(stored_image.get("path"), FINDY2_MEDIA_DIR)
                return
            if snap_photo_picker in page.overlay:
                page.overlay.remove(snap_photo_picker)
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
                compose_top_bar("스냅 작성", go_back_from_snap_write, submit_snap),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=18, vertical=14),
                    bgcolor="#FFFFFF",
                    border_radius=26,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.52, BORDER_COLOR)),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("분야", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_800),
                                    snap_category_row,
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            title_field,
                            note_field,
                            snap_photo_preview,
                            compose_bottom_toolbar([
                                compose_bottom_action(("IMAGE_OUTLINED", "PHOTO_LIBRARY_OUTLINED"), "사진", pick_snap_photos),
                                compose_bottom_action(("PLACE_OUTLINED", "LOCATION_ON_OUTLINED"), "장소", lambda e: show_snack("장소 첨부는 곧 연결될 예정이에요.")),
                                compose_bottom_action(("TAG", "NUMBERS"), "태그", lambda e: show_snack("설명에 #태그를 입력해보세요.")),
                                ft.Container(expand=True),
                                snap_photo_count,
                            ]),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=10,
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

        related_items = [x for x in get_snap_feed_items(app_state.get("snap_sort_mode", "popular"), app_state.get("snap_filter", "전체")) if x["id"] != item["id"]][:6]
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
            persist_user_data()
            refresh_snap_action_controls()
            update_snap_action_controls()

        def toggle_snap_save(e):
            saved_ids = app_state.setdefault("snap_saved_ids", set())
            if item_id in saved_ids:
                saved_ids.discard(item_id)
            else:
                saved_ids.add(item_id)
            persist_user_data()
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
                soft_button(
                    f'{item["category"]} 커뮤니티 보기',
                    MAIN_COLOR,
                    "white",
                    lambda e: (
                        app_state.__setitem__("community_category_filter", item["category"]),
                        show_community_board_page("자유", selected_tab=2),
                    ),
                    width=content_width(),
                ),
                ft.Container(height=24),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_video_detail_page(video=None):
        target_video = video or app_state.get("video_detail_item")
        if target_video:
            app_state["video_detail_item"] = target_video
            target_category = target_video.get("category", "전체")
            app_state["video_category_filter"] = target_category
            target_key = video_key(target_video)
            target_list = [
                item
                for item in get_all_video_items()
                if normalize_overlay_category_name(item.get("category")) == normalize_overlay_category_name(target_category)
            ] or get_all_video_items()
            app_state["active_video_index"] = next(
                (idx for idx, item in enumerate(target_list) if video_key(item) == target_key),
                0,
            )
            show_video_page()
            return
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
            persist_user_data()
            refresh_actions()
            update_actions()

        def toggle_save(e):
            if key in saved_ids:
                saved_ids.discard(key)
            else:
                saved_ids.add(key)
            persist_user_data()
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
            persist_user_data()
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

        video_categories = ["전체", "헤어", "네일아트", "메이크업", "반영구", "웨딩", "포토"]
        selected_cat = app_state.get("video_category_filter", "전체")

        all_videos = get_all_video_items()
        normalized_video_filter = normalize_content_filter(selected_cat)
        filtered = (
            all_videos
            if normalized_video_filter == "전체"
            else [v for v in all_videos if normalize_overlay_category_name(v.get("category")) == normalized_video_filter]
        )
        if not filtered:
            filtered = all_videos
            selected_cat = "전체"
            app_state["video_category_filter"] = "전체"

        video_view_height = full_phone_height() - 64
        slide_direction = app_state.pop("video_slide_direction", 0)
        active_index = max(0, min(app_state.get("active_video_index", 0), len(filtered) - 1))
        app_state["active_video_index"] = active_index
        active_video = filtered[active_index]
        active_key = video_key(active_video)
        liked_ids = app_state.setdefault("video_liked_keys", set())
        saved_ids = app_state.setdefault("video_saved_keys", set())
        followed_creators = app_state.setdefault("video_followed_creators", set())
        reposted_ids = app_state.setdefault("video_reposted_keys", set())
        shared_ids = app_state.setdefault("video_shared_keys", set())
        paused_ids = app_state.setdefault("video_paused_keys", set())
        drag_state = {"dy": 0}
        app_state.setdefault("video_more_open", False)

        def choose_cat(cat):
            def handler(e):
                app_state["video_category_filter"] = cat
                app_state["active_video_index"] = 0
                app_state["video_comments_open"] = False
                app_state["video_more_open"] = False
                app_state["video_category_drawer"] = None
                show_video_page()
            return handler

        def toggle_video_category_drawer(e=None):
            app_state["video_category_drawer"] = None if app_state.get("video_category_drawer") == "category" else "category"
            app_state["video_comments_open"] = False
            app_state["video_more_open"] = False
            show_video_page()

        def move_video(delta):
            def handler(e):
                next_index = active_index + delta
                if next_index < 0 or next_index >= len(filtered):
                    show_snack("표시할 영상이 더 없어요.")
                    return
                app_state["active_video_index"] = next_index
                app_state["video_slide_direction"] = 1 if delta > 0 else -1
                app_state["video_comments_open"] = False
                app_state["video_more_open"] = False
                show_video_page()
            return handler

        def toggle_video_like(e):
            if active_key in liked_ids:
                liked_ids.discard(active_key)
            else:
                liked_ids.add(active_key)
            persist_user_data()
            show_video_page()

        def toggle_video_save(e):
            if active_key in saved_ids:
                saved_ids.discard(active_key)
            else:
                saved_ids.add(active_key)
            persist_user_data()
            show_video_page()

        def toggle_video_repost(e=None):
            if active_key in reposted_ids:
                reposted_ids.discard(active_key)
                show_snack("리포스트를 취소했어요.")
            else:
                reposted_ids.add(active_key)
                show_snack("내 활동에 리포스트했어요.")
            persist_user_data()
            show_video_page()

        def share_video(e=None):
            shared_ids.add(active_key)
            show_snack("공유 링크가 준비되었어요.")
            show_video_page()

        def toggle_video_more(e=None):
            app_state["video_more_open"] = not app_state.get("video_more_open", False)
            show_video_page()

        def close_video_more(e=None):
            app_state["video_more_open"] = False
            show_video_page()

        def toggle_video_play(e=None):
            if active_key in paused_ids:
                paused_ids.discard(active_key)
                show_snack("비디오를 재생해요.")
            else:
                paused_ids.add(active_key)
                show_snack("비디오를 일시정지했어요.")
            show_video_page()

        comment_count = {"value": int(active_video.get("comments", 0) or 0)}
        video_comments_store = app_state.setdefault("video_comments", {})
        if active_key not in video_comments_store:
            video_comments_store[active_key] = [
                {"author": "ms.j7755", "time": "4시간", "text": "이 팁 진짜 바로 써먹을 수 있겠어요.", "likes": "405", "replies": 3},
                {"author": "tjdsalon", "time": "7시간", "text": "분위기랑 설명이 깔끔해서 보기 편해요.", "likes": "1,003", "replies": 1},
                {"author": "bbo__2", "time": "10분", "text": "@findy_user 이 스타일 저장해둘게요.", "likes": "1", "replies": 0},
                {"author": "ksykangta", "time": "7시간", "text": "다음에는 제품 정보도 같이 알려주세요.", "likes": "90", "replies": 0},
                {"author": "im99bo88", "time": "6시간", "text": "어휴 보는 데 너무 유용하네요.", "likes": "22", "replies": 1},
            ]
        active_comments = video_comments_store[active_key]
        comment_count["value"] = max(comment_count["value"], len(active_comments))
        active_video["comments"] = comment_count["value"]
        comment_field = ft.TextField(
            width=full_phone_width() - 150,
            height=44,
            hint_text="회원님의 생각을 남겨보세요.",
            border=ft.InputBorder.NONE,
            bgcolor=ft.Colors.with_opacity(0.13, "#F5EDE5"),
            border_radius=999,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=9),
            text_style=ft.TextStyle(size=13, color="#FFFFFF", weight=ft.FontWeight.W_700),
            hint_style=ft.TextStyle(size=13, color=ft.Colors.with_opacity(0.68, "#F5EDE5")),
        )

        def open_video_comments(e=None):
            app_state["video_comments_open"] = True
            app_state["video_more_open"] = False
            show_video_page()

        def close_video_comments(e=None):
            app_state["video_comments_open"] = False
            show_video_page()

        def submit_reel_comment(e=None):
            text = (comment_field.value or "").strip()
            if not text:
                show_snack("댓글을 입력해주세요.", bgcolor="#B85C5C")
                return
            profile = get_user_profile()
            active_comments.insert(0, {
                "userId": current_user_id(),
                "author": profile.get("username") or profile.get("name") or "FINDY 회원",
                "time": "방금 전",
                "text": text,
                "likes": "0",
                "replies": 0,
            })
            active_video["comments"] = len(active_comments)
            app_state["video_comments_open"] = True
            persist_user_data()
            show_video_page()

        def on_video_drag_start(e):
            drag_state["dy"] = 0

        def on_video_drag_update(e):
            drag_state["dy"] += getattr(e, "delta_y", 0) or 0

        def on_video_drag_end(e):
            dy = drag_state.get("dy", 0)
            velocity = getattr(e, "velocity_y", 0) or getattr(e, "primary_velocity", 0) or 0
            # FINDY2 reels order: swiping up moves 1 -> 2 -> 3, swiping down moves back.
            if dy < -52 or velocity < -700:
                move_video(1)(e)
            elif dy > 52 or velocity > 700:
                move_video(-1)(e)
            drag_state["dy"] = 0

        def metric_label(value, fallback="0"):
            return str(value if value not in (None, "") else fallback)

        def creator_name(video):
            return video.get("creatorName") or video.get("profileName") or video.get("nickname") or f'{video.get("category", "FINDY")}러'

        def video_profile_avatar(name):
            return ft.Container(
                width=38,
                height=38,
                border_radius=19,
                bgcolor=ft.Colors.with_opacity(0.92, "#FFFFFF"),
                border=ft.border.all(1, ft.Colors.with_opacity(0.62, "#FFFFFF")),
                alignment=ft.Alignment(0, 0),
                content=ft.Text((name or "F")[0], size=15, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_900),
            )

        active_creator = creator_name(active_video)

        def open_video_profile(e=None):
            show_snack(f"{active_creator}님의 프로필은 곧 연결될 예정이에요.")

        def toggle_follow_creator(e=None):
            if active_creator in followed_creators:
                followed_creators.discard(active_creator)
                show_snack("팔로우를 취소했어요.")
            else:
                followed_creators.add(active_creator)
                show_snack(f"{active_creator}님을 팔로우했어요.")
            persist_user_data()
            show_video_page()

        def reels_action(icon_name, count, on_click=None, active=False):
            return ft.Container(
                width=58,
                height=76,
                on_click=on_click,
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=23,
                            bgcolor=ft.Colors.with_opacity(0.92, "#F4EEE8") if active else ft.Colors.with_opacity(0.18, "#FFFFFF"),
                            border=ft.border.all(1, ft.Colors.with_opacity(0.70, MAIN_COLOR if active else "#FFFFFF")),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon(icon_name), size=27, color=MAIN_COLOR_DARK if active else "#FFFFFF"),
                        ),
                        ft.Text(metric_label(count), size=11, color="#F7F2EC", weight=ft.FontWeight.W_900, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=3,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            )

        def comment_avatar(author):
            return ft.Container(
                width=38,
                height=38,
                border_radius=19,
                bgcolor=ft.Colors.with_opacity(0.90, "#FFFFFF"),
                alignment=ft.Alignment(0, 0),
                content=ft.Text((author or "F")[0].upper(), size=13, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_900),
            )

        def video_comment_row(comment):
            replies = int(comment.get("replies", 0) or 0)
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                content=ft.Row(
                    controls=[
                        comment_avatar(comment.get("author")),
                        ft.Column(
                            controls=[
                                ft.Text(f'{comment.get("author", "FINDY 회원")} {comment.get("time", "")}', size=11, color=ft.Colors.with_opacity(0.74, "#FFFFFF"), weight=ft.FontWeight.W_800),
                                ft.Text(comment.get("text", ""), size=13, color="#FFFFFF", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text("답글 달기", size=10, color=ft.Colors.with_opacity(0.58, "#FFFFFF"), weight=ft.FontWeight.W_700),
                                ft.Container(
                                    padding=ft.padding.only(left=22, top=3),
                                    visible=replies > 0,
                                    content=ft.Text(f"답글 {replies}개 보기", size=10, color=ft.Colors.with_opacity(0.48, "#FFFFFF"), weight=ft.FontWeight.W_800),
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Column(
                            controls=[
                                ft.Icon(app_icon("FAVORITE_BORDER"), size=23, color=ft.Colors.with_opacity(0.78, "#FFFFFF")),
                                ft.Text(str(comment.get("likes", "0")), size=10, color=ft.Colors.with_opacity(0.70, "#FFFFFF"), weight=ft.FontWeight.W_800),
                            ],
                            spacing=3,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            )

        def add_reaction(emoji):
            def handler(e=None):
                comment_field.value = f"{comment_field.value or ''}{emoji}"
                try:
                    comment_field.update()
                except Exception:
                    pass
            return handler

        def video_comments_panel():
            reactions = ["❤️", "🙌", "🔥", "👏", "🥲", "😍", "😮", "😂"]
            return ft.Container(
                left=0,
                right=0,
                bottom=0,
                height=390,
                bgcolor="#15110E",
                border_radius=ft.border_radius.only(top_left=26, top_right=26),
                border=ft.border.only(top=ft.BorderSide(1, ft.Colors.with_opacity(0.32, MAIN_COLOR))),
                shadow=ft.BoxShadow(blur_radius=22, color="#77000000", offset=ft.Offset(0, -8)),
                content=ft.Column(
                    controls=[
                        ft.Container(width=44, height=3, bgcolor=ft.Colors.with_opacity(0.58, MAIN_COLOR), border_radius=999, margin=ft.margin.only(top=12, bottom=6), alignment=ft.Alignment(0, 0)),
                        ft.Row(
                            controls=[
                                ft.Text(f"댓글 {len(active_comments)}", size=15, color="#F7F2EC", weight=ft.FontWeight.W_900, expand=True),
                                ft.Container(width=32, height=32, border_radius=16, bgcolor=ft.Colors.with_opacity(0.12, "#FFFFFF"), alignment=ft.Alignment(0, 0), on_click=close_video_comments, ink=True, content=ft.Icon(app_icon("CLOSE"), size=20, color="#F7F2EC")),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            height=206,
                            content=ft.ListView(
                                controls=[video_comment_row(comment) for comment in active_comments],
                                spacing=0,
                                padding=0,
                            ),
                        ),
                        ft.Container(height=1, bgcolor=ft.Colors.with_opacity(0.08, "#FFFFFF")),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=34,
                                    height=34,
                                    border_radius=17,
                                    alignment=ft.Alignment(0, 0),
                                    on_click=add_reaction(emoji),
                                    ink=True,
                                    content=ft.Text(emoji, size=22),
                                )
                                for emoji in reactions
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        ),
                        ft.Row(
                            controls=[
                                profile_avatar(44, get_user_profile()),
                                comment_field,
                                ft.Container(width=34, height=34, border_radius=17, alignment=ft.Alignment(0, 0), on_click=lambda e: show_snack("댓글 사진 첨부는 곧 연결될 예정이에요."), ink=True, content=ft.Icon(app_icon("IMAGE_OUTLINED", "PHOTO_LIBRARY_OUTLINED"), size=23, color=ft.Colors.with_opacity(0.90, "#F7F2EC"))),
                                ft.Container(width=36, height=36, border_radius=18, bgcolor=MAIN_COLOR, alignment=ft.Alignment(0, 0), on_click=submit_reel_comment, ink=True, content=ft.Icon(app_icon("SEND"), size=20, color="#FFFFFF")),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=9,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=16),
            )

        def video_background():
            video_path = active_video.get("video_path") or active_video.get("path") or active_video.get("src")
            is_paused = active_key in paused_ids
            if video_path:
                return ft.Video(
                    playlist=[ft.VideoMedia(resource=video_path)],
                    width=full_phone_width(),
                    height=video_view_height,
                    autoplay=not is_paused,
                    show_controls=False,
                    muted=False,
                    fit=ft.ImageFit.COVER,
                    playlist_mode=ft.PlaylistMode.LOOP,
                    fill_color="#0B0705",
                )
            return ft.Stack(
                controls=[
                    ft.Container(
                        width=full_phone_width(),
                        height=video_view_height,
                        bgcolor="#090604",
                        content=ft.Stack(
                            controls=[
                                ft.Container(left=-40, top=90, width=220, height=220, border_radius=110, bgcolor=ft.Colors.with_opacity(0.12, MAIN_COLOR)),
                                ft.Container(right=-52, bottom=180, width=260, height=260, border_radius=130, bgcolor=ft.Colors.with_opacity(0.10, "#F4EEE8")),
                                ft.Container(alignment=ft.Alignment(0, -0.26), content=ft.Text(active_video.get("category", "FINDY"), size=48, color=ft.Colors.with_opacity(0.14, "#F4EEE8"), weight=ft.FontWeight.W_900)),
                            ],
                        ),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Container(
                            width=92,
                            height=92,
                            border_radius=46,
                            bgcolor=ft.Colors.with_opacity(0.92, "#F4EEE8"),
                            alignment=ft.Alignment(0, 0),
                            on_click=toggle_video_play,
                            ink=True,
                            content=ft.Icon(app_icon("PLAY_ARROW" if is_paused else "PAUSE", "PLAY_CIRCLE"), size=48, color="#0B0705"),
                        ),
                    ),
                ],
            )

        like_count = active_video.get("likes") or active_video.get("views") or "0"
        share_count = active_video.get("shares") or "1.7만"
        save_count = active_video.get("saves") or "3.1만"

        def video_category_option(cat):
            active = cat == selected_cat
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=11, vertical=7),
                bgcolor=MAIN_COLOR if active else ft.Colors.with_opacity(0.12, "#F4EEE8"),
                border_radius=999,
                border=ft.border.all(1, MAIN_COLOR if active else ft.Colors.with_opacity(0.24, "#F4EEE8")),
                on_click=choose_cat(cat),
                ink=True,
                content=ft.Text(cat, size=11, color="#FFFFFF" if active else "#F4EEE8", weight=ft.FontWeight.W_900 if active else ft.FontWeight.W_700),
            )

        video_category_button = ft.Container(
            padding=ft.padding.symmetric(horizontal=13, vertical=9),
            bgcolor=ft.Colors.with_opacity(0.16, "#F4EEE8"),
            border_radius=999,
            border=ft.border.all(1, ft.Colors.with_opacity(0.32, "#F4EEE8")),
            on_click=toggle_video_category_drawer,
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Text("분야", size=11, color=ft.Colors.with_opacity(0.78, "#F4EEE8"), weight=ft.FontWeight.W_800),
                    ft.Text(selected_cat, size=12, color="#F7F2EC", weight=ft.FontWeight.W_900),
                    ft.Icon(app_icon("KEYBOARD_ARROW_UP" if app_state.get("video_category_drawer") == "category" else "KEYBOARD_ARROW_DOWN", "EXPAND_MORE"), size=17, color="#F7F2EC"),
                ],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
        )

        category_bar = ft.Column(
            controls=[
                ft.Row(controls=[video_category_button], alignment=ft.MainAxisAlignment.START),
                *([
                    ft.Container(
                        width=content_width(),
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        bgcolor=ft.Colors.with_opacity(0.88, "#15110E"),
                        border_radius=22,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.28, MAIN_COLOR)),
                        content=ft.Row(
                            controls=[video_category_option(cat) for cat in video_categories],
                            spacing=7,
                            wrap=True,
                        ),
                    )
                ] if app_state.get("video_category_drawer") == "category" else []),
            ],
            spacing=8,
        )

        def more_sheet_action(icon_name, title, subtitle, on_click):
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=11),
                border_radius=14,
                on_click=on_click,
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=17,
                            bgcolor=ft.Colors.with_opacity(0.16, MAIN_COLOR),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon(icon_name), size=19, color=MAIN_COLOR),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(title, size=13, color="#F7F2EC", weight=ft.FontWeight.W_900),
                                ft.Text(subtitle, size=10, color=ft.Colors.with_opacity(0.68, "#F7F2EC")),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def video_more_panel():
            return ft.Container(
                right=12,
                bottom=232,
                width=238,
                padding=ft.padding.all(10),
                bgcolor=ft.Colors.with_opacity(0.96, "#15110E"),
                border_radius=20,
                border=ft.border.all(1, ft.Colors.with_opacity(0.28, MAIN_COLOR)),
                shadow=ft.BoxShadow(blur_radius=22, color="#77000000", offset=ft.Offset(0, 8)),
                content=ft.Column(
                    controls=[
                        more_sheet_action("BOOKMARK_BORDER", "저장", "나중에 다시 볼 비디오로 보관", lambda e: (toggle_video_save(e), close_video_more())),
                        more_sheet_action("TUNE", "나의 FINDY에 반영", "이런 영상 추천을 더 보여줘요", lambda e: (show_snack("나의 FINDY 추천에 반영했어요."), close_video_more())),
                        more_sheet_action("REPORT_OUTLINED", "신고", "불편한 콘텐츠를 운영 검토로 보내요", lambda e: (show_snack("신고가 접수되었어요."), close_video_more())),
                    ],
                    spacing=2,
                ),
            )

        video_stage = ft.GestureDetector(
            on_vertical_drag_start=on_video_drag_start,
            on_vertical_drag_update=on_video_drag_update,
            on_vertical_drag_end=on_video_drag_end,
            content=ft.Container(
                width=full_phone_width(),
                height=video_view_height,
                bgcolor="#090604",
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Stack(
                    controls=[
                        ft.Container(width=full_phone_width(), height=video_view_height, content=video_background()),
                        ft.Container(left=0, right=0, top=0, height=150, bgcolor=ft.Colors.with_opacity(0.38, "#090604")),
                        ft.Container(left=0, right=0, bottom=0, height=250, bgcolor=ft.Colors.with_opacity(0.48, "#090604")),
                        ft.Container(
                            alignment=ft.Alignment(0, 0),
                            content=ft.Container(
                                width=82,
                                height=82,
                                border_radius=41,
                                bgcolor=ft.Colors.with_opacity(0.88, "#F4EEE8"),
                                border=ft.border.all(1, ft.Colors.with_opacity(0.50, MAIN_COLOR)),
                                alignment=ft.Alignment(0, 0),
                                on_click=toggle_video_play,
                                ink=True,
                                visible=active_key in paused_ids,
                                content=ft.Icon(app_icon("PLAY_ARROW"), size=45, color="#0B0705"),
                            ),
                        ),
                        ft.Container(
                                top=22,
                                left=22,
                                right=22,
                                content=ft.Stack(
                                    controls=[
                                        ft.Container(
                                            width=34,
                                            height=34,
                                            border_radius=17,
                                            bgcolor=ft.Colors.with_opacity(0.14, "#F4EEE8"),
                                            alignment=ft.Alignment(0, 0),
                                            on_click=lambda e: (app_state.__setitem__("current_page", "write_video"), show_write_video_page()),
                                            ink=True,
                                            content=ft.Icon(app_icon("ADD"), size=28, color="#F7F2EC"),
                                        ),
                                        ft.Container(
                                            alignment=ft.Alignment(1, 0),
                                            content=ft.Container(
                                                padding=ft.padding.symmetric(horizontal=9, vertical=5),
                                                bgcolor=ft.Colors.with_opacity(0.14, "#F4EEE8"),
                                                border_radius=999,
                                                content=ft.Text(f"{active_index + 1}/{len(filtered)}", size=12, color="#F7F2EC", weight=ft.FontWeight.W_900),
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ft.Container(top=68, left=20, right=20, content=category_bar),
                        ft.Container(
                            right=12,
                            bottom=118,
                            content=ft.Column(
                                controls=[
                                    reels_action("FAVORITE" if active_key in liked_ids else "FAVORITE_BORDER", like_count, toggle_video_like, active_key in liked_ids),
                                    reels_action("CHAT_BUBBLE_OUTLINE", comment_count["value"] or 137, open_video_comments),
                                    reels_action("AUTORENEW", share_count, toggle_video_repost, active_key in reposted_ids),
                                    reels_action("SEND_OUTLINED", save_count, share_video, active_key in shared_ids),
                                    ft.Container(
                                        width=46,
                                        height=42,
                                        border_radius=21,
                                        bgcolor=ft.Colors.with_opacity(0.18, "#FFFFFF") if not app_state.get("video_more_open") else ft.Colors.with_opacity(0.92, "#F4EEE8"),
                                        border=ft.border.all(1, ft.Colors.with_opacity(0.70, "#FFFFFF" if not app_state.get("video_more_open") else MAIN_COLOR)),
                                        alignment=ft.Alignment(0, 0),
                                        on_click=toggle_video_more,
                                        ink=True,
                                        content=ft.Icon(app_icon("MORE_HORIZ", "MORE_VERT"), size=25, color="#FFFFFF" if not app_state.get("video_more_open") else MAIN_COLOR_DARK),
                                    ),
                                    ft.Container(height=10),
                                    ft.Container(
                                        width=42,
                                        height=42,
                                        border_radius=12,
                                        bgcolor=ft.Colors.with_opacity(0.88, "#FFFFFF"),
                                        alignment=ft.Alignment(0, 0),
                                        on_click=lambda e: (show_findy_recommendation_page(reset_draft=True)),
                                        ink=True,
                                        content=brand_mark(32),
                                    ),
                                ],
                                spacing=4,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ),
                        ft.Container(
                            left=18,
                            right=86,
                            bottom=96,
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Container(on_click=open_video_profile, ink=True, content=video_profile_avatar(active_creator)),
                                            ft.Column(
                                                controls=[
                                                    ft.Text(f"{active_creator}님", size=13, color="#F7F2EC", weight=ft.FontWeight.W_900),
                                                    ft.Text(f'{active_video.get("badge", "TIP")} · 조회 {active_video.get("views", "0")} · {active_video.get("duration", "0:59")}', size=11, color=ft.Colors.with_opacity(0.78, "#F7F2EC")),
                                                ],
                                                spacing=2,
                                                expand=True,
                                            ),
                                            ft.Container(
                                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                                bgcolor=MAIN_COLOR if active_creator not in followed_creators else ft.Colors.with_opacity(0.16, "#F4EEE8"),
                                                border=ft.border.all(1, MAIN_COLOR if active_creator not in followed_creators else ft.Colors.with_opacity(0.40, "#F4EEE8")),
                                                border_radius=999,
                                                on_click=toggle_follow_creator,
                                                ink=True,
                                                content=ft.Text("팔로우" if active_creator not in followed_creators else "팔로잉", size=12, color="#FFFFFF", weight=ft.FontWeight.W_900),
                                            ),
                                        ],
                                        spacing=9,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.Text(active_video.get("title", "비디오"), size=17, color="#F7F2EC", weight=ft.FontWeight.W_900, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(active_video.get("subtitle", "FINDY 회원의 뷰티 팁"), size=12, color=ft.Colors.with_opacity(0.84, "#F7F2EC"), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text("아래에서 위로 올리면 다음 · 위에서 아래로 내리면 이전", size=10, color=ft.Colors.with_opacity(0.62, "#F7F2EC"), max_lines=1),
                                    ft.Container(width=content_width() - 12, height=2, bgcolor=ft.Colors.with_opacity(0.40, MAIN_COLOR), border_radius=2),
                                ],
                                spacing=7,
                            ),
                        ),
                        *([video_more_panel()] if app_state.get("video_more_open") else []),
                        *([video_comments_panel()] if app_state.get("video_comments_open") else []),
                    ],
                ),
            ),
        )

        slide_offset = 0
        if slide_direction > 0:
            slide_offset = 0.92
        elif slide_direction < 0:
            slide_offset = -0.92

        video_surface = ft.Container(
            width=full_phone_width(),
            height=video_view_height,
            offset=ft.Offset(0, slide_offset),
            opacity=0.34 if slide_direction else 1,
            animate_offset=ft.Animation(190, ft.AnimationCurve.EASE_OUT),
            animate_opacity=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            content=video_stage,
        )

        body = ft.Container(
            width=full_phone_width(),
            height=video_view_height,
            bgcolor="#090604",
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=video_surface,
        )

        make_shell(body, app_state["selected_tab"])

        if slide_direction:
            async def animate_video_slide():
                await asyncio.sleep(0.01)
                try:
                    video_surface.offset = ft.Offset(0, 0)
                    video_surface.opacity = 1
                    video_surface.update()
                except Exception:
                    page.update()

            page.run_task(animate_video_slide)

    def show_write_video_page():
        close_overlays()
        app_state["selected_tab"] = 3
        app_state["current_page"] = "write_video"

        selected_category = [app_state.get("video_category_filter", "전체")]
        if selected_category[0] == "전체":
            selected_category[0] = "헤어"
        selected_video_path = [None]
        selected_video_info = [None]
        video_name_text = ft.Text("선택된 영상이 없어요.", size=12, color=SUBTEXT_COLOR)
        video_preview = ft.Container(
            width=content_width() - 36,
            height=190,
            visible=False,
            border_radius=18,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor="#120D0A",
        )

        title_field = compose_text_field("팁 제목을 입력해주세요.", size=20, weight=ft.FontWeight.W_900)
        subtitle_field = compose_text_field(
            "어떤 팁인지 짧게 설명해주세요.\n#30초팁 #루틴 #스타일링...",
            multiline=True,
            min_lines=8,
            max_lines=12,
            size=14,
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
            source_path = selected_file.path or selected_file.name
            try:
                metadata = validate_video_file(source_path)
            except MediaStorageError as error:
                selected_video_path[0] = None
                selected_video_info[0] = None
                video_preview.visible = False
                video_name_text.value = "선택된 영상이 없어요."
                show_snack(str(error), bgcolor="#B85C5C")
                page.update()
                return
            selected_video_path[0] = metadata["sourcePath"]
            selected_video_info[0] = metadata
            size_mb = metadata["size"] / (1024 * 1024)
            video_name_text.value = f"{metadata['name']} · {size_mb:.1f}MB"
            video_preview.visible = True
            video_preview.content = ft.Stack(
                controls=[
                    ft.Video(
                        playlist=[ft.VideoMedia(resource=metadata["sourcePath"])],
                        width=content_width() - 36,
                        height=190,
                        fit=ft.ImageFit.CONTAIN,
                        autoplay=False,
                        muted=True,
                        show_controls=True,
                        on_error=lambda event: show_snack("영상 미리보기를 재생하지 못했어요.", bgcolor="#B85C5C"),
                    ),
                    ft.Container(
                        right=8,
                        top=8,
                        width=30,
                        height=30,
                        border_radius=15,
                        bgcolor=ft.Colors.with_opacity(0.78, "#000000"),
                        alignment=ft.Alignment(0, 0),
                        ink=True,
                        on_click=lambda event: clear_selected_video(),
                        content=ft.Icon(app_icon("CLOSE"), size=17, color="#FFFFFF"),
                    ),
                ],
            )
            page.update()

        def clear_selected_video():
            selected_video_path[0] = None
            selected_video_info[0] = None
            video_name_text.value = "선택된 영상이 없어요."
            video_preview.visible = False
            video_preview.content = None
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
            try:
                stored_video = store_video(
                    selected_video_path[0],
                    FINDY2_MEDIA_DIR,
                    current_user_id(),
                )
            except MediaStorageError as error:
                show_snack(str(error), bgcolor="#B85C5C")
                return
            profile = get_user_profile()
            new_video = {
                "id": f"user_video_{int(datetime.now().timestamp())}",
                "userId": current_user_id(),
                "title": title,
                "subtitle": subtitle or "FINDY 회원이 올린 뷰티 팁",
                "badge": "TIP",
                "category": selected_category[0],
                "duration": "0:59",
                "views": "0",
                "video_path": stored_video["path"],
                "videoMetadata": stored_video,
                "creatorName": profile.get("name", "FINDY 회원"),
                "profileName": profile.get("username", ""),
            }
            app_state.setdefault("written_videos", []).insert(0, new_video)
            app_state["video_category_filter"] = selected_category[0]
            if not persist_user_data(notify_on_error=True):
                app_state["written_videos"].remove(new_video)
                remove_media_file(stored_video.get("path"), FINDY2_MEDIA_DIR)
                return
            cleanup_file_picker()
            open_completion_feedback(
                "팁 비디오가 등록되었어요",
                "작성한 팁은 비디오 화면에서 확인할 수 있어요.",
                "비디오 보기",
                "video",
                selected_tab=3,
                icon_name="PLAY_CIRCLE",
            )

        body = ft.Column(
            controls=[
                compose_top_bar("팁 비디오", go_back, submit_video),
                ft.Container(
                    width=content_width(),
                    padding=ft.padding.symmetric(horizontal=18, vertical=14),
                    bgcolor="#FFFFFF",
                    border_radius=26,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.52, BORDER_COLOR)),
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                width=content_width(),
                                height=48,
                                border_radius=999,
                                border=ft.border.all(1.2, BORDER_COLOR),
                                bgcolor=MAIN_COLOR_SOFT,
                                on_click=pick_video,
                                ink=True,
                                padding=ft.padding.symmetric(horizontal=14),
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.VIDEO_FILE_OUTLINED, size=18, color=MAIN_COLOR),
                                        ft.Text("비디오 선택", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_900),
                                        ft.Container(expand=True),
                                        video_name_text,
                                    ],
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ),
                            ft.Text("MP4, MOV, M4V, WEBM 형식의 짧은 뷰티 팁을 올려주세요.", size=11, color=SUBTEXT_COLOR),
                            video_preview,
                            category_row,
                            title_field,
                            subtitle_field,
                            compose_bottom_toolbar([
                                compose_bottom_action(("MOVIE_OUTLINED", "SMART_DISPLAY_OUTLINED"), "동영상", pick_video),
                                compose_bottom_action(("PLACE_OUTLINED", "LOCATION_ON_OUTLINED"), "장소", lambda e: show_snack("장소 첨부는 곧 연결될 예정이에요.")),
                                compose_bottom_action(("TAG", "NUMBERS"), "태그", lambda e: show_snack("설명에 #태그를 입력해보세요.")),
                            ]),
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(height=24),
            ],
            spacing=10,
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

        app_state["selected_subcategory"] = None

        recent_defaults = ["레이어드컷", "여쿨 메이크업", "네일 유지력", "프로필 촬영", "반영구 눈썹"]
        recent_searches = app_state.setdefault("recent_searches", recent_defaults.copy())

        search_field = ft.TextField(
            value=app_state.get("search_text", ""),
            hint_text="궁금한 뷰티 글을 검색해보세요.",
            expand=True,
            height=42,
            border=ft.InputBorder.NONE,
            bgcolor=ft.Colors.TRANSPARENT,
            cursor_color=MAIN_COLOR,
            text_size=13,
            text_style=ft.TextStyle(size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
            hint_style=ft.TextStyle(size=13, color=ft.Colors.with_opacity(0.48, SUBTEXT_COLOR)),
            content_padding=ft.padding.symmetric(horizontal=0, vertical=4),
        )

        def add_recent_search(query):
            query = (query or "").strip()
            if not query:
                return
            current = app_state.setdefault("recent_searches", [])
            app_state["recent_searches"] = [query] + [item for item in current if item != query]
            app_state["recent_searches"] = app_state["recent_searches"][:8]
            persist_user_data()

        def run_search(e=None, query=None):
            entered_text = (query if query is not None else search_field.value or "").strip()
            if not entered_text:
                show_snack("검색어를 입력해주세요.", bgcolor="#B85C5C")
                return
            add_recent_search(entered_text)
            app_state["search_text"] = entered_text
            app_state["selected_category"] = None
            app_state["selected_subcategory"] = "통합검색"
            app_state["search_results"] = build_global_search_results(entered_text)
            app_state["recommendation_entry"] = entered_text
            app_state["category_browse_mode"] = True
            app_state["search_results_back_target"] = "search"
            app_state["current_page"] = "search_results"
            show_search_results_page()

        search_field.on_submit = lambda e: run_search()

        def remove_recent(term):
            def handler(e):
                app_state["recent_searches"] = [item for item in app_state.get("recent_searches", []) if item != term]
                persist_user_data()
                show_search_page()
            return handler

        def clear_recent(e=None):
            app_state["recent_searches"] = []
            persist_user_data()
            show_search_page()

        def open_community_type(label):
            def handler(e):
                app_state["community_category_filter"] = "전체"
                show_community_board_page(label, selected_tab=0)
            return handler

        def quick_item(label, icon_names, color, on_click):
            return ft.Container(
                width=54,
                on_click=on_click,
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=15,
                            bgcolor=ft.Colors.with_opacity(0.12, color),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(app_icon(*icon_names), size=22, color=color),
                        ),
                        ft.Text(
                            label,
                            size=10,
                            color=TEXT_COLOR,
                            weight=ft.FontWeight.W_700,
                            text_align=ft.TextAlign.CENTER,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=7,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def recent_row(term):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=4, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.42, BORDER_COLOR))),
                on_click=lambda e, selected=term: run_search(query=selected),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon("HISTORY", "SCHEDULE"), size=19, color=ft.Colors.with_opacity(0.72, SUBTEXT_COLOR)),
                        ft.Text(term, size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_700, expand=True),
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=16,
                            alignment=ft.Alignment(0, 0),
                            on_click=remove_recent(term),
                            ink=True,
                            content=ft.Icon(app_icon("CLOSE", "CANCEL"), size=18, color=ft.Colors.with_opacity(0.68, SUBTEXT_COLOR)),
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        top_search_bar = ft.Container(
            width=content_width(),
            padding=ft.padding.only(left=2, right=0, top=4, bottom=2),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=20,
                        alignment=ft.Alignment(0, 0),
                        on_click=safe_go_back,
                        ink=True,
                        content=ft.Icon(app_icon("ARROW_BACK_IOS_NEW", "ARROW_BACK"), size=23, color=TEXT_COLOR),
                    ),
                    ft.Container(
                        height=46,
                        expand=True,
                        padding=ft.padding.only(left=14, right=8),
                        bgcolor=ft.Colors.with_opacity(0.78, CHIP_BG),
                        border_radius=17,
                        content=ft.Row(
                            controls=[
                                ft.Icon(app_icon("SEARCH", "SEARCH_OUTLINED"), size=19, color=ft.Colors.with_opacity(0.62, SUBTEXT_COLOR)),
                                search_field,
                                ft.Container(
                                    width=32,
                                    height=32,
                                    border_radius=12,
                                    alignment=ft.Alignment(0, 0),
                                    bgcolor=ft.Colors.with_opacity(0.42, "#FFFFFF"),
                                    on_click=lambda e: show_snack("사진 검색은 곧 연결될 예정이에요."),
                                    ink=True,
                                    content=ft.Icon(app_icon("PHOTO_CAMERA_OUTLINED", "CAMERA_ALT_OUTLINED"), size=18, color=SUBTEXT_COLOR),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Container(
                        width=46,
                        height=40,
                        border_radius=18,
                        alignment=ft.Alignment(0, 0),
                        on_click=safe_go_back,
                        ink=True,
                        content=ft.Text("닫기", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                    ),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        quick_categories = ft.Container(
            width=content_width(),
            padding=ft.padding.only(top=12, bottom=8),
            content=ft.Row(
                controls=[
                    quick_item("리뷰", ("RATE_REVIEW_OUTLINED", "RATE_REVIEW"), "#F28A2E", open_community_type("리뷰")),
                    quick_item("질문", ("HELP_OUTLINE", "CONTACT_SUPPORT_OUTLINED"), "#4BA36B", open_community_type("질문")),
                    quick_item("자유", ("FORUM_OUTLINED", "CHAT_BUBBLE_OUTLINE"), "#8A63F7", open_community_type("자유")),
                    quick_item("스냅", ("PHOTO_LIBRARY_OUTLINED", "IMAGE_OUTLINED"), "#D95C96", lambda e: go_snap_page()),
                    quick_item("비디오", ("SMART_DISPLAY_OUTLINED", "PLAY_CIRCLE_OUTLINE"), "#9B7658", lambda e: go_video_page()),
                    quick_item("자유", ("MENU", "APPS"), MAIN_COLOR_DARK, open_community_type("자유")),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        findy_tip = ft.Container(
            width=content_width(),
            padding=ft.padding.symmetric(horizontal=14, vertical=13),
            bgcolor=ft.Colors.with_opacity(0.74, CHIP_BG),
            border_radius=18,
            on_click=open_community_type("자유"),
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=30,
                        height=30,
                        border_radius=15,
                        bgcolor=ft.Colors.with_opacity(0.16, MAIN_COLOR),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(app_icon("AUTO_AWESOME", "STARS"), size=18, color=MAIN_COLOR),
                    ),
                    ft.Text("지금 FINDY에서 많이 보는 리뷰와 질문을 확인해보세요.", size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800, expand=True),
                    ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=SUBTEXT_COLOR),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        body = ft.Column(
            controls=[
                top_search_bar,
                quick_categories,
                ft.Container(height=8),
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            ft.Text("FINDY 추천", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True),
                            ft.Text("더보기", size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                findy_tip,
                ft.Container(height=14),
                ft.Container(
                    width=content_width(),
                    content=ft.Row(
                        controls=[
                            ft.Text("최근 검색", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True),
                            ft.Container(
                                on_click=clear_recent,
                                ink=True,
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=6, vertical=4),
                                content=ft.Text("전체 삭제", size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                *([recent_row(term) for term in app_state.get("recent_searches", [])] or [
                    ft.Container(
                        width=content_width(),
                        padding=ft.padding.symmetric(vertical=24),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("최근 검색어가 없어요.", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_600),
                    )
                ]),
                ft.Container(height=20),
            ],
            spacing=6,
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
            "관련 콘텐츠를 정리 중...",
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
                        "FINDY가 관련 글을 찾고 있어요",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "검색어와 관심 분야에 맞는 리뷰, 질문, 스냅을 정리하는 중...",
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
            (0, "관련 콘텐츠를 정리 중..."),
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

        is_artist_mode = browse_mode and app_state.get("selected_subcategory") == "아티스트"
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
            header_title = f"{app_state.get('selected_subcategory', '')} 전체 보기" if browse_mode else "검색 결과"

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
                            ft.Text("서비스 리뷰 작성", size=13, color=MAIN_COLOR, weight=ft.FontWeight.W_600, expand=True),
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
                empty_title = "조건에 맞는 목록이 없어요"
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
            if not is_artist_mode:
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
                                on_click=lambda e, category=item.get("category", item.get("title")): open_category_recommendations(category, "커뮤니티"),
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
                    elif item.get("type") == "community":
                        cards.append(community_result_card(item, back_page="search_results"))
                    elif item.get("type") == "video":
                        cards.append(
                            browse_result_card(
                                item,
                                on_click=lambda e, selected_video=item.get("source", item): show_video_detail_page(selected_video),
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
        show_saved_content_page(app_state.get("saved_content_type", "전체"))

    def show_category_page():
        clear_transient_ui()
        app_state["selected_tab"] = 0
        app_state["current_page"] = "category"

        def open_category_overview(sub_category):
            open_content_category(sub_category, "전체")

        def category_page_intro():
            return ft.Container(
                width=content_width(),
                padding=ft.padding.only(left=4, right=4, top=2, bottom=6),
                content=ft.Column(
                    controls=[
                        ft.Text("카테고리", size=24, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        ft.Text(
                            "원하는 콘텐츠와 뷰티 분야를 빠르게 골라보세요.",
                            size=12,
                            color=SUBTEXT_COLOR,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=5,
                ),
            )

        def grouped_category_row(icon_name, title, description, on_click, icon_label=None, is_last=False):
            return ft.Container(
                padding=ft.padding.only(left=18, right=16, top=13, bottom=0 if is_last else 0),
                on_click=on_click,
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=38,
                                    height=38,
                                    border_radius=12,
                                    bgcolor=MAIN_COLOR_SOFT,
                                    border=ft.border.all(1, ft.Colors.with_opacity(0.45, BORDER_COLOR)),
                                    alignment=ft.Alignment(0, 0),
                                    content=(
                                        ft.Text(icon_label, size=14, color=MAIN_COLOR, weight=ft.FontWeight.W_900)
                                        if icon_label
                                        else ft.Icon(app_icon(icon_name), size=20, color=MAIN_COLOR)
                                    ),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(title, size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                        ft.Text(description, size=11, color=SUBTEXT_COLOR, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=17, color=ft.Colors.with_opacity(0.62, SUBTEXT_COLOR)),
                            ],
                            spacing=13,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            height=1,
                            margin=ft.margin.only(left=51, top=12),
                            bgcolor=ft.Colors.with_opacity(0.58, BORDER_COLOR),
                            visible=not is_last,
                        ),
                    ],
                    spacing=0,
                ),
            )

        def grouped_category_section(rows):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.only(top=2, bottom=14),
                bgcolor=CARD_COLOR,
                border_radius=24,
                border=ft.border.all(1, ft.Colors.with_opacity(0.58, BORDER_COLOR)),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=18, color="#0B8B6B4F", offset=ft.Offset(0, 8)),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Column(controls=rows, spacing=0),
            )

        beauty_category_entries = [
            {"label": "헤어", "icon": "CONTENT_CUT", "description": "컷, 펌, 컬러와 스타일링"},
            {"label": "네일아트", "icon": "BRUSH", "description": "젤, 케어, 디자인 네일"},
            {"label": "메이크업", "icon": "FACE_RETOUCHING_NATURAL", "description": "데일리, 촬영, 웨딩 메이크업"},
            {"label": "포토", "icon": "PHOTO_CAMERA", "description": "프로필, 스냅, 콘셉트 촬영"},
            {"label": "웨딩", "icon": "DIAMOND", "description": "본식, 리허설, 신부 뷰티"},
            {"label": "반영구시술", "icon": "AUTO_FIX_HIGH", "description": "눈썹, 아이라인, 입술 시술"},
        ]

        content_rows = [
            grouped_category_row(
                item["icon"],
                "FINDY 스냅" if item["key"] == "스냅" else "FINDY 비디오" if item["key"] == "비디오" else item["label"],
                item["description"],
                lambda e, key=item["key"]: open_category_overview(key),
                icon_label=("F" if item["key"] in {"스냅", "비디오"} else None),
                is_last=index == len(content_category_entries) - 1,
            )
            for index, item in enumerate(content_category_entries)
        ]

        beauty_rows = [
            grouped_category_row(
                item["icon"],
                item["label"],
                item["description"],
                lambda e, category=item["label"]: show_beauty_category_page(category),
                is_last=index == len(beauty_category_entries) - 1,
            )
            for index, item in enumerate(beauty_category_entries)
        ]

        body = ft.Column(
            controls=[
                category_page_intro(),
                grouped_category_section(content_rows),
                grouped_category_section(beauty_rows),
                ft.Container(height=24),
            ],
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        make_shell(body, app_state["selected_tab"])

    def show_legal_page(initial_document=None):
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "legal"
        selected_document = app_state.setdefault(
            "selected_legal_document",
            "개인정보 처리방침",
        )
        if initial_document and initial_document in LEGAL_DOCUMENTS:
            selected_document = initial_document
            app_state["selected_legal_document"] = initial_document

        def select_document(title):
            app_state["selected_legal_document"] = title
            show_legal_page(title)

        tabs = ft.Row(
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=9),
                    border_radius=18,
                    bgcolor=MAIN_COLOR if title == selected_document else "#FFFFFF",
                    border=ft.border.all(1, MAIN_COLOR if title == selected_document else BORDER_COLOR),
                    ink=True,
                    on_click=lambda e, name=title: select_document(name),
                    content=ft.Text(
                        title,
                        size=11,
                        color="#FFFFFF" if title == selected_document else TEXT_COLOR,
                        weight=ft.FontWeight.W_800,
                    ),
                )
                for title in LEGAL_DOCUMENTS
            ],
            spacing=8,
            scroll=ft.ScrollMode.HIDDEN,
        )

        sections = []
        for title, body in LEGAL_DOCUMENTS[selected_document]:
            sections.append(
                ft.Container(
                    width=content_width(),
                    padding=18,
                    bgcolor="#FFFFFF",
                    border_radius=18,
                    border=ft.border.all(1, BORDER_COLOR),
                    content=ft.Column(
                        controls=[
                            ft.Text(title, size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                            ft.Text(body, size=12, color=SUBTEXT_COLOR, selectable=True),
                        ],
                        spacing=8,
                    ),
                )
            )

        controls = [
            page_header("정책 안내", on_back=go_back_page),
            ft.Text(
                f"마지막 업데이트: {LEGAL_UPDATED_AT}",
                width=content_width(),
                size=11,
                color=SUBTEXT_COLOR,
            ),
            ft.Container(width=content_width(), content=tabs),
            *sections,
            ft.Container(height=24),
        ]
        make_shell(
            ft.Column(
                controls=controls,
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            app_state["selected_tab"],
        )

    def show_connected_accounts_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "connected_accounts"

        current_user = app_state.get("current_user") or {}
        linked_identities = {
            item.get("provider"): item
            for item in current_user.get("identities", [])
            if item.get("provider")
        }
        status_text = ft.Text(
            "",
            width=content_width(),
            size=11,
            color="#B85C5C",
            weight=ft.FontWeight.W_700,
        )

        def provider_row(provider_key, is_last=False):
            provider = SOCIAL_PROVIDERS[provider_key]
            identity = linked_identities.get(provider_key)
            linked = identity is not None
            email = str((identity or {}).get("email") or "").strip()

            def connect_provider(event=None):
                page.run_task(
                    perform_social_auth,
                    provider_key,
                    status_text,
                    None,
                    True,
                )

            return ft.Container(
                width=content_width() - 36,
                padding=ft.padding.symmetric(vertical=13),
                border=(
                    None
                    if is_last
                    else ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR))
                ),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=38,
                            height=38,
                            border_radius=13,
                            bgcolor=provider["background"],
                            border=ft.border.all(
                                1,
                                "#E4E4E4"
                                if provider_key in {"google", "kakao"}
                                else provider["background"],
                            ),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Image(
                                src=provider["asset"],
                                width=21,
                                height=21,
                                fit=ft.ImageFit.CONTAIN,
                            ),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    provider["label"],
                                    size=14,
                                    color=TEXT_COLOR,
                                    weight=ft.FontWeight.W_800,
                                ),
                                ft.Text(
                                    email if linked and email else (
                                        "FINDY 통합회원에 연결됨"
                                        if linked
                                        else "추가 로그인 수단으로 연결할 수 있어요."
                                    ),
                                    size=10,
                                    color=SUBTEXT_COLOR,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(
                                horizontal=12,
                                vertical=8,
                            ),
                            border_radius=14,
                            bgcolor=MAIN_COLOR_SOFT if linked else MAIN_COLOR,
                            ink=not linked,
                            on_click=None if linked else connect_provider,
                            content=ft.Text(
                                "연결됨" if linked else "연결하기",
                                size=10,
                                color=MAIN_COLOR_DARK if linked else "#FFFFFF",
                                weight=ft.FontWeight.W_800,
                            ),
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        provider_keys = list(SOCIAL_PROVIDERS)
        provider_rows = [
            provider_row(
                provider_key,
                is_last=index == len(provider_keys) - 1,
            )
            for index, provider_key in enumerate(provider_keys)
        ]

        email_account = bool(
            current_user.get("email")
            and not str(current_user.get("email")).endswith("@social.findy.local")
        )
        controls = [
            page_header("연결된 계정", on_back=go_back_page),
            ft.Text(
                "여러 로그인 수단을 하나의 FINDY 계정에 연결해도 글, 저장, 프로필은 그대로 유지됩니다.",
                width=content_width(),
                size=12,
                color=SUBTEXT_COLOR,
            ),
            status_text,
            ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=18, vertical=8),
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=provider_rows,
                    spacing=0,
                ),
            ),
            ft.Container(
                width=content_width(),
                padding=18,
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            app_icon("MAIL_OUTLINE"),
                            size=24,
                            color=MAIN_COLOR,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "이메일 로그인",
                                    size=14,
                                    color=TEXT_COLOR,
                                    weight=ft.FontWeight.W_800,
                                ),
                                ft.Text(
                                    current_user.get("email", "")
                                    if email_account
                                    else "이메일 비밀번호는 등록되지 않았어요.",
                                    size=10,
                                    color=SUBTEXT_COLOR,
                                ),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Text(
                            "사용 중" if email_account else "미등록",
                            size=10,
                            color=MAIN_COLOR_DARK if email_account else SUBTEXT_COLOR,
                            weight=ft.FontWeight.W_800,
                        ),
                    ],
                    spacing=12,
                ),
            ),
            ft.Container(height=24),
        ]
        make_shell(
            ft.Column(
                controls=controls,
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            app_state["selected_tab"],
        )

    def show_settings_page():
        clear_transient_ui()
        close_overlays()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "settings"

        settings = app_state.setdefault(
            "app_settings",
            {
                "pushNotifications": True,
                "activityNotifications": True,
                "reviewNotifications": True,
                "soundEffects": True,
                "vibration": True,
                "privateProfile": False,
                "activityStatus": True,
                "personalizedRecommendations": True,
                "autoPlayVideos": True,
                "dataSaver": False,
                "highContrastText": False,
                "cacheSize": "128MB",
                "language": "한국어",
                "region": "대한민국",
            },
        )

        def update_setting(key, value):
            settings[key] = value
            persist_user_data()
            page.update()

        def open_coming_soon(title):
            def handler(e=None):
                show_snack(f"{title} 설정은 곧 세부 화면으로 연결될 예정이에요.")
            return handler

        def setting_switch(title, subtitle, key):
            return ft.Container(
                width=content_width() - 36,
                padding=ft.padding.symmetric(vertical=12),
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(title, size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.Switch(
                            value=bool(settings.get(key)),
                            active_color=MAIN_COLOR,
                            on_change=lambda e, selected_key=key: update_setting(selected_key, e.control.value),
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def setting_row(icon_name, title, subtitle, value="", on_click=None):
            trailing = []
            if value:
                trailing.append(ft.Text(value, size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700))
            trailing.append(ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=SUBTEXT_COLOR))
            return ft.Container(
                width=content_width() - 36,
                padding=ft.padding.symmetric(vertical=13),
                on_click=on_click or open_coming_soon(title),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=24, color=TEXT_COLOR),
                        ft.Column(
                            controls=[
                                ft.Text(title, size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        *trailing,
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def settings_section(title, rows):
            return ft.Container(
                width=content_width(),
                padding=ft.padding.symmetric(horizontal=18, vertical=16),
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, ft.Colors.with_opacity(0.34, BORDER_COLOR)),
                content=ft.Column(
                    controls=[
                        ft.Text(title, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        *rows,
                    ],
                    spacing=2,
                ),
            )

        controls = [
            page_header("설정", on_back=go_back_page),
            ft.Text("앱 사용 방식, 알림, 개인정보, 콘텐츠 추천 기준을 관리해요.", size=13, color=SUBTEXT_COLOR, width=content_width()),
            settings_section(
                "알림",
                [
                    setting_switch("푸시 알림", "댓글, 답변, 저장 반응을 받을지 선택해요.", "pushNotifications"),
                    setting_switch("활동 알림", "내 글의 좋아요와 댓글 알림을 받아요.", "activityNotifications"),
                    setting_switch("리뷰 알림", "리뷰 상태 변경과 신고 처리 알림을 받아요.", "reviewNotifications"),
                ],
            ),
            settings_section(
                "소리와 재생",
                [
                    setting_switch("앱 소리", "버튼, 반응, 완료 안내음을 켜거나 꺼요.", "soundEffects"),
                    setting_switch("진동", "좋아요나 저장 같은 터치 반응 진동을 사용해요.", "vibration"),
                    setting_switch("비디오 자동 재생", "FINDY 비디오에 들어가면 자동으로 재생해요.", "autoPlayVideos"),
                ],
            ),
            settings_section(
                "개인정보와 보안",
                [
                    setting_switch("비공개 프로필", "내 프로필과 작성글 노출 범위를 제한해요.", "privateProfile"),
                    setting_switch("활동 상태 표시", "최근 활동 여부를 다른 사용자에게 보여줘요.", "activityStatus"),
                    setting_row(
                        "LINK",
                        "연결된 계정",
                        "네이버, 카카오, Google, Apple 로그인 연결을 관리해요.",
                        on_click=lambda e: show_connected_accounts_page(),
                    ),
                    setting_row("LOCK_OUTLINE", "계정 보안", "로그인 기기, 비밀번호, 2단계 인증을 관리해요."),
                    setting_row("BLOCK", "차단/숨김 관리", "차단한 사용자와 숨긴 글을 확인해요."),
                ],
            ),
            settings_section(
                "콘텐츠와 추천",
                [
                    setting_switch("맞춤 추천", "나의 FINDY와 활동을 추천에 반영해요.", "personalizedRecommendations"),
                    setting_row("TUNE", "나의 FINDY", "헤어, 네일아트, 메이크업 등 추천 기준을 조정해요.", on_click=lambda e: show_findy_recommendation_page(reset_draft=True)),
                    setting_row("HISTORY", "시청/검색 기록", "최근 본 글과 검색 기록을 관리해요."),
                ],
            ),
            settings_section(
                "앱 환경",
                [
                    setting_switch("데이터 절약 모드", "이미지와 비디오 로딩을 가볍게 사용해요.", "dataSaver"),
                    setting_switch("글자 대비 높이기", "텍스트를 더 선명하게 표시해요.", "highContrastText"),
                    setting_row("LANGUAGE", "언어", "앱 표시 언어", settings.get("language", "한국어")),
                    setting_row("PUBLIC", "지역", "추천 콘텐츠 기준 지역", settings.get("region", "대한민국")),
                    setting_row("STORAGE", "저장공간", "캐시와 임시 파일 관리", settings.get("cacheSize", "0MB")),
                ],
            ),
            settings_section(
                "지원과 정보",
                [
                    setting_row("HELP_OUTLINE", "도움말", "앱 이용 방법과 자주 묻는 질문", on_click=lambda e: show_support_page()),
                    setting_row(
                        "DESCRIPTION_OUTLINED",
                        "약관 및 개인정보 처리방침",
                        "서비스 정책과 데이터 이용 기준",
                        on_click=lambda e: show_legal_page(),
                    ),
                    setting_row("INFO_OUTLINE", "앱 정보", "FINDY2 beta · 커뮤니티 데이터 수집 버전"),
                    setting_row(
                        "PERSON_REMOVE_OUTLINED",
                        "계정 삭제",
                        "계정과 이 기기에 저장된 데이터를 영구 삭제해요.",
                        on_click=open_account_deletion_dialog,
                    ),
                ],
            ),
            ft.Container(height=24),
        ]
        make_shell(ft.Column(controls=controls, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.CENTER), app_state["selected_tab"])

    def show_my_page():
        clear_transient_ui()
        app_state["selected_tab"] = 4
        app_state["current_page"] = "my"

        profile = get_user_profile()
        point_balance = len(app_state.get("written_reviews", [])) * 120 + len(app_state.get("community_posts", [])) * 40 + len(app_state.get("written_videos", [])) * 80

        def my_card(content, padding=18, on_click=None):
            return ft.Container(
                width=content_width(),
                padding=padding,
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.border.all(1, ft.Colors.with_opacity(0.34, BORDER_COLOR)),
                on_click=on_click,
                ink=bool(on_click),
                content=content,
            )

        def service_tile(icon_name, label, color, on_click):
            return ft.Container(
                width=(content_width() - 44) / 2,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                on_click=on_click,
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=27, color=color),
                        ft.Text(label, size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def coming_soon_service(e=None):
            show_snack("준비 중인 서비스예요.")

        def quick_action(icon_name, label, on_click, dot=False):
            return ft.Container(
                expand=True,
                on_click=on_click,
                ink=True,
                content=ft.Column(
                    controls=[
                        ft.Stack(
                            controls=[
                                ft.Icon(app_icon(icon_name), size=27, color=TEXT_COLOR),
                                ft.Container(width=7, height=7, right=0, top=0, border_radius=4, bgcolor=MAIN_COLOR, visible=dot),
                            ],
                        ),
                        ft.Text(label, size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                    ],
                    spacing=7,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def section_row(icon_name, title, subtitle, on_click, badge=None):
            return ft.Container(
                width=content_width() - 36,
                padding=ft.padding.symmetric(vertical=13),
                on_click=on_click,
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Icon(app_icon(icon_name), size=25, color=TEXT_COLOR),
                        ft.Column(
                            controls=[
                                ft.Text(title, size=14, color=TEXT_COLOR, weight=ft.FontWeight.W_800),
                                ft.Text(subtitle, size=11, color=SUBTEXT_COLOR, visible=bool(subtitle)),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            bgcolor=MAIN_COLOR_SOFT,
                            border_radius=999,
                            visible=bool(badge),
                            content=ft.Text(str(badge or ""), size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_800),
                        ),
                        ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=17, color=SUBTEXT_COLOR),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def section_card(title, rows):
            return my_card(
                ft.Column(
                    controls=[
                        ft.Text(title, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                        *rows,
                    ],
                    spacing=2,
                ),
                padding=ft.padding.symmetric(horizontal=18, vertical=16),
            )

        controls = [
            my_card(
                ft.Row(
                    controls=[
                        profile_avatar(62, profile),
                        ft.Column(
                            controls=[
                                ft.Text(profile.get("name") or "FINDY 회원", size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_900, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(profile.get("username") or "findy_user", size=12, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                ft.Row(
                                    controls=[
                                        ft.Text("프로필 확인", size=11, color=SUBTEXT_COLOR, weight=ft.FontWeight.W_700),
                                    ],
                                    spacing=7,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=19, color=SUBTEXT_COLOR),
                    ],
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda e: show_profile_page(),
            ),
            my_card(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("FINDY 포인트", size=14, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_900, expand=True),
                                ft.Text(f"{point_balance:,}P", size=17, color=TEXT_COLOR, weight=ft.FontWeight.W_900),
                                ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=17, color=SUBTEXT_COLOR),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(expand=True, alignment=ft.Alignment(-1, 0), content=ft.Text("충전", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800)),
                                ft.Container(width=1, height=16, bgcolor=BORDER_COLOR),
                                ft.Container(expand=True, alignment=ft.Alignment(-1, 0), content=ft.Text("선물", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_800)),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                                    bgcolor="#20242A",
                                    border_radius=999,
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(app_icon("AUTO_AWESOME"), size=15, color="#FFFFFF"),
                                            ft.Text("활동 보상", size=12, color="#FFFFFF", weight=ft.FontWeight.W_900),
                                        ],
                                        spacing=5,
                                    ),
                                ),
                            ],
                            spacing=16,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=17,
                ),
            ),
            my_card(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("서비스", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_900, expand=True),
                                ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=17, color=SUBTEXT_COLOR),
                            ],
                        ),
                        ft.Row(
                            controls=[
                                service_tile("ARTICLE_OUTLINED", "내가 쓴글", MAIN_COLOR, lambda e: show_my_content_page("전체")),
                                service_tile("FAVORITE_BORDER", "좋아요", "#E257A8", lambda e: show_liked_content_page("전체")),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                service_tile("BOOKMARK_BORDER", "저장", "#8D6AF3", lambda e: show_saved_content_page("전체")),
                                service_tile("TUNE", "나의 FINDY", MAIN_COLOR, lambda e: show_findy_recommendation_page(reset_draft=True)),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                service_tile("SETTINGS_OUTLINED", "설정", "#F28B22", lambda e: show_settings_page()),
                                service_tile("EVENT_AVAILABLE", "내 예약", "#4F86C6", open_reservation_entry),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                service_tile("LOCAL_ACTIVITY", "쿠폰", "#C08A32", coming_soon_service),
                                service_tile("RATE_REVIEW_OUTLINED", "후기", "#8B6B4F", lambda e: show_my_reviews_page()),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                service_tile("NOTIFICATIONS_NONE", "알림", "#F28B22", open_notifications_page),
                                service_tile("CELEBRATION", "이벤트", "#D85C7A", coming_soon_service),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=10,
                ),
            ),
            section_card(
                "고객 지원",
                [
                    section_row("CAMPAIGN", "공지사항", "업데이트와 운영 안내", lambda e: show_notice_page()),
                    section_row("LIGHTBULB_OUTLINE", "개선 의견", "원하는 기능을 남겨주세요.", lambda e: show_feedback_page()),
                    section_row("SUPPORT_AGENT", "문의내역", "1:1 문의와 답변 확인", lambda e: show_inquiry_page()),
                ],
            ),
            logout_button(),
            ft.Container(height=24),
        ]

        body = ft.Column(
            controls=controls,
            spacing=12,
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
                show_snack("서비스 항목을 선택해주세요.", bgcolor="#B85C5C")
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
        for service in available_services or [form.get("service") or "기본 서비스"]:
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
                            ft.Text("운영 시간과 휴무일을 반영해서 예약 가능한 날짜만 보여드려요.", size=12, color=SUBTEXT_COLOR),
                            ft.Container(height=SPACE_SM),
                            ft.Text("서비스 선택", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                            ft.Text("선택한 분야에서 제공하는 항목만 표시돼요.", size=12, color=SUBTEXT_COLOR),
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
                                        ft.Text(f'서비스: {selected_service or "선택 전"}', size=12, color=SUBTEXT_COLOR),
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
                            confirm_row("서비스", form.get("service", "기본 서비스")),
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
            open_reservation_entry()

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
                            ft.Text("예약 정보가 안전하게 저장되었어요.", size=12, color=SUBTEXT_COLOR, text_align=ft.TextAlign.CENTER),
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
                                                ft.Text("담당자", size=12, color=SUBTEXT_COLOR, expand=True),
                                                ft.Text(completed.get("artist_name", ""), size=12, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                                            ],
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Text("서비스", size=12, color=SUBTEXT_COLOR, expand=True),
                                                ft.Text(completed.get("service", completed.get("category", "기본 서비스")), size=12, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
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
            if not FINDY2_RESERVATION_ENABLED:
                show_future_reservation_page()
                return
            reset_reservation_form(artist)
            show_snack("예약 화면으로 이동해요.")
            show_reservation_page()

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
                page_header("프로필", on_back=go_back),
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
                                        expand=True,
                                        height=48,
                                        border_radius=RADIUS_MD,
                                        bgcolor=MAIN_COLOR,
                                        alignment=ft.Alignment(0, 0),
                                        on_click=reserve_click,
                                        ink=True,
                                        content=ft.Text("예약 준비중" if not FINDY2_RESERVATION_ENABLED else "예약하기", size=13, color="#FFFFFF", weight=ft.FontWeight.W_800),
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
                                            ft.Text("사진과 영상으로 스타일 분위기를 확인해보세요.", size=12, color=SUBTEXT_COLOR),
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

    def handle_page_error(event):
        error_message = getattr(event, "data", None) or getattr(event, "error", None) or "unknown page error"
        show_runtime_error_page(error_message)

    def handle_page_resized(event):
        app_state["_resize_generation"] = app_state.get("_resize_generation", 0) + 1
        generation = app_state["_resize_generation"]

        async def rerender_after_resize():
            await asyncio.sleep(0.12)
            if generation != app_state.get("_resize_generation"):
                return
            if app_state.get("current_page") == "opening":
                return
            render_current_page()

        page.run_task(rerender_after_resize)

    def handle_disconnect(event):
        if app_state.get("current_user"):
            persist_user_data()

    page.on_error = handle_page_error
    page.on_resized = handle_page_resized
    page.on_disconnect = handle_disconnect

    await start_opening_flow()

if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR if os.path.isdir(ASSETS_DIR) else None)
