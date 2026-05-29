import os
import flet as ft

from components.cards import page_header, auth_button, hero_card, soft_button
from components.layout import (
    CONTENT_WIDTH,
    FIELD_WIDTH,
    SPACE_LG,
    MAIN_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
    BORDER_COLOR,
)
from core import router
from .common import shell


def render(page, app_state, rerender):
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

    def asset_path(filename: str) -> str:
        return os.path.join(assets_dir, filename)

    email_field = ft.TextField(
        width=FIELD_WIDTH,
        hint_text="이메일",
        border_radius=16,
        bgcolor="#FFFFFF",
        border_color=BORDER_COLOR,
        focused_border_color=MAIN_COLOR,
        cursor_color=MAIN_COLOR,
        content_padding=14,
    )

    password_field = ft.TextField(
        width=FIELD_WIDTH,
        hint_text="비밀번호",
        password=True,
        can_reveal_password=True,
        border_radius=16,
        bgcolor="#FFFFFF",
        border_color=BORDER_COLOR,
        focused_border_color=MAIN_COLOR,
        cursor_color=MAIN_COLOR,
        content_padding=14,
    )

    def go_home(e):
        router.go_home()
        rerender(page)

    def go_opening(e):
        router.go("opening")
        rerender(page)

    social_buttons = ft.Column(
        controls=[
            auth_button("Apple로 계속하기", asset_path("apple.png"), on_click=go_home, width=CONTENT_WIDTH),
            auth_button("Google로 계속하기", asset_path("google.png"), on_click=go_home, width=CONTENT_WIDTH),
            auth_button("Kakao로 계속하기", asset_path("kakao.png"), on_click=go_home, width=CONTENT_WIDTH),
            auth_button("Naver로 계속하기", asset_path("naver.png"), on_click=go_home, width=CONTENT_WIDTH),
        ],
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    body = ft.Column(
        controls=[
            page_header(
                "로그인",
                on_back=go_opening,
                width=CONTENT_WIDTH,
                subtitle="브랜드 감성을 유지한 채 더 빠르게 시작할 수 있어요.",
            ),
            hero_card(
                "Welcome back",
                "계정을 연결하면 예약, 저장한 뷰티, 내역이 자연스럽게 이어져요.",
                CONTENT_WIDTH,
                emoji="✨",
            ),
            ft.Container(
                width=CONTENT_WIDTH,
                padding=ft.padding.all(18),
                bgcolor="#FFFFFF",
                border_radius=24,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text("이메일 로그인", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        email_field,
                        password_field,
                        soft_button("이메일로 로그인", MAIN_COLOR, "white", go_home, width=FIELD_WIDTH),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            ft.Row(
                controls=[
                    ft.Container(expand=True, height=1, bgcolor="#EDE5DB"),
                    ft.Text("또는", size=11, color=SUBTEXT_COLOR),
                    ft.Container(expand=True, height=1, bgcolor="#EDE5DB"),
                ],
                width=CONTENT_WIDTH,
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            social_buttons,
            ft.Container(
                width=CONTENT_WIDTH,
                alignment=ft.Alignment(0, 0),
                content=ft.Text(
                    "로그인하면 FINDY의 저장 기능과 예약 흐름을 더 편하게 이용할 수 있어요.",
                    size=11,
                    color=SUBTEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
            ),
        ],
        spacing=SPACE_LG,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
