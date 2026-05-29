import os
import flet as ft

from components.cards import primary_button, ghost_button
from components.layout import (
    CONTENT_WIDTH,
    SPACE_LG,
    SPACE_XL,
    SPACE_2XL,
    MAIN_COLOR_DARK,
    TEXT_STRONG,
    SUBTEXT_COLOR,
    OPENING_IMAGE,
)
from core import router
from .common import shell


def render(page, app_state, rerender):
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    opening_image_path = os.path.join(assets_dir, OPENING_IMAGE)

    hero_visual = (
        ft.Container(
            width=CONTENT_WIDTH,
            height=300,
            border_radius=28,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Image(
                src=opening_image_path,
                width=CONTENT_WIDTH,
                height=300,
                fit="cover",
            ),
        )
        if os.path.exists(opening_image_path)
        else ft.Container(
            width=CONTENT_WIDTH,
            height=300,
            border_radius=28,
            bgcolor="#FFFFFF",
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                controls=[
                    ft.Text("FINDY", size=32, weight=ft.FontWeight.W_500, color=MAIN_COLOR_DARK),
                    ft.Text("Find Your Beauty", size=12, color=SUBTEXT_COLOR),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )
    )

    def go_login(e):
        router.go("login")
        rerender(page)

    headline = ft.Container(
        width=CONTENT_WIDTH,
        padding=ft.padding.symmetric(horizontal=4),
        content=ft.Column(
            controls=[
                ft.Text(
                    "Find Your Beauty",
                    size=13,
                    weight=ft.FontWeight.W_500,
                    color=MAIN_COLOR_DARK,
                ),
                ft.Container(height=6),
                ft.Text(
                    "오늘의 무드에 어울리는\n뷰티 아티스트를 만나보세요.",
                    size=24,
                    weight=ft.FontWeight.W_500,
                    color=TEXT_STRONG,
                ),
                ft.Container(height=10),
                ft.Text(
                    "탐색·스냅·예약까지 자연스럽게 이어지는 FINDY 경험.",
                    size=12,
                    weight=ft.FontWeight.W_400,
                    color=SUBTEXT_COLOR,
                ),
            ],
            spacing=0,
        ),
    )

    body = ft.Column(
        controls=[
            ft.Container(height=SPACE_LG),
            hero_visual,
            ft.Container(height=SPACE_2XL),
            headline,
            ft.Container(height=SPACE_2XL),
            primary_button(
                "로그인하고 시작하기",
                go_login,
                width=CONTENT_WIDTH,
                height=56,
            ),
            ghost_button(
                "이미 계정이 있어요",
                go_login,
                width=CONTENT_WIDTH,
            ),
            ft.Container(height=SPACE_LG),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
