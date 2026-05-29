import os
import flet as ft

from components.cards import page_header, auth_button, primary_button, text_field
from components.layout import (
    CONTENT_WIDTH,
    FIELD_WIDTH,
    SPACE_LG,
    SPACE_XL,
    SPACE_2XL,
    MAIN_COLOR_DARK,
    TEXT_STRONG,
    SUBTEXT_COLOR,
    BORDER_COLOR,
    LOGIN_BRAND_IMAGE,
)
from core import router
from .common import shell


def render(page, app_state, rerender):
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

    def asset_path(filename: str) -> str:
        return os.path.join(assets_dir, filename)

    logo_path = asset_path(LOGIN_BRAND_IMAGE)

    brand_mark = (
        ft.Image(
            src=logo_path,
            width=72,
            height=72,
            fit="contain",
        )
        if os.path.exists(logo_path)
        else ft.Container(
            width=72,
            height=72,
            border_radius=999,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, BORDER_COLOR),
            alignment=ft.Alignment(0, 0),
            content=ft.Text("F", size=28, weight=ft.FontWeight.W_500, color=MAIN_COLOR_DARK),
        )
    )

    email_field = text_field("이메일", width=FIELD_WIDTH)
    password_field = text_field("비밀번호", width=FIELD_WIDTH, password=True, can_reveal_password=True)

    def go_home(e):
        router.go_home()
        rerender(page)

    def go_opening(e):
        router.go("opening")
        rerender(page)

    brand_block = ft.Container(
        width=CONTENT_WIDTH,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            controls=[
                brand_mark,
                ft.Container(height=12),
                ft.Text(
                    "다시 만나서 반가워요",
                    size=20,
                    weight=ft.FontWeight.W_500,
                    color=TEXT_STRONG,
                ),
                ft.Text(
                    "계정을 연결하면 예약과 저장한 뷰티가 자연스럽게 이어져요.",
                    size=12,
                    weight=ft.FontWeight.W_400,
                    color=SUBTEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    email_block = ft.Container(
        width=CONTENT_WIDTH,
        content=ft.Column(
            controls=[
                email_field,
                password_field,
                primary_button("이메일로 로그인", go_home, width=FIELD_WIDTH, height=52),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    divider = ft.Row(
        controls=[
            ft.Container(expand=True, height=1, bgcolor=BORDER_COLOR),
            ft.Text("또는", size=11, weight=ft.FontWeight.W_400, color=SUBTEXT_COLOR),
            ft.Container(expand=True, height=1, bgcolor=BORDER_COLOR),
        ],
        width=CONTENT_WIDTH,
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

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
            ),
            ft.Container(height=SPACE_LG),
            brand_block,
            ft.Container(height=SPACE_XL),
            email_block,
            ft.Container(height=SPACE_LG),
            divider,
            ft.Container(height=SPACE_LG),
            social_buttons,
            ft.Container(height=SPACE_LG),
            ft.Container(
                width=CONTENT_WIDTH,
                alignment=ft.Alignment(0, 0),
                content=ft.Text(
                    "로그인하면 FINDY의 저장과 예약 흐름을 더 편하게 이용할 수 있어요.",
                    size=11,
                    weight=ft.FontWeight.W_400,
                    color=SUBTEXT_COLOR,
                    text_align=ft.TextAlign.CENTER,
                ),
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
