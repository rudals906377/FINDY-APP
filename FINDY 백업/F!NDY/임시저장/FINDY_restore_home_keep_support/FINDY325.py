import os
import flet as ft

from components.layout import APP_FONT, BG_COLOR
from core.app_state import app_state
from pages import (
    opening_page,
    login_page,
    home_page,
    category_page,
    snap_page,
    video_page,
    my_page,
    detail_page,
    reservation_page,
    reservation_confirm_page,
    reservation_complete_page,
    reservation_history_page,
    support_page,
    inquiry_page,
)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


async def main(page: ft.Page):
    page.title = "FINDY324"
    regular_font = os.path.join(ASSETS_DIR, "Pretendard-Regular.ttf")
    bold_font = os.path.join(ASSETS_DIR, "Pretendard-Bold.ttf")
    if os.path.exists(regular_font) and os.path.exists(bold_font):
        page.fonts = {
            "Pretendard": "assets/Pretendard-Regular.ttf",
            "Pretendard-Bold": "assets/Pretendard-Bold.ttf",
        }
        page.theme = ft.Theme(font_family="Pretendard")
        page.font_family = APP_FONT
    else:
        page.theme = ft.Theme()

    page.window.width = 520
    page.window.height = 920
    page.padding = 0
    page.bgcolor = BG_COLOR
    page.scroll = ft.ScrollMode.HIDDEN
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def render(target_page=None):
        target_page = target_page or page
        page_name = app_state.get("current_page", "opening")

        if page_name == "opening":
            opening_page.render(target_page, app_state, render)
        elif page_name == "login":
            login_page.render(target_page, app_state, render)
        elif page_name == "home":
            home_page.render(target_page, app_state, render)
        elif page_name == "category":
            category_page.render(target_page, app_state, render)
        elif page_name == "snap":
            snap_page.render(target_page, app_state, render)
        elif page_name == "video":
            video_page.render(target_page, app_state, render)
        elif page_name == "my":
            my_page.render(target_page, app_state, render)
        elif page_name == "detail":
            detail_page.render(target_page, app_state, render)
        elif page_name == "reservation":
            reservation_page.render(target_page, app_state, render)
        elif page_name == "reservation_confirm":
            reservation_confirm_page.render(target_page, app_state, render)
        elif page_name == "reservation_complete":
            reservation_complete_page.render(target_page, app_state, render)
        elif page_name == "reservation_history":
            reservation_history_page.render(target_page, app_state, render)
        elif page_name == "support":
            support_page.render(target_page, app_state, render)
        elif page_name == "inquiry":
            inquiry_page.render(target_page, app_state, render)
        else:
            opening_page.render(target_page, app_state, render)

    render(page)
