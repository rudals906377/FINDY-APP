import os
import flet as ft

from components.cards import hero_card, soft_button
from components.layout import (
    CONTENT_WIDTH,
    SPACE_MD,
    MAIN_COLOR,
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
        ft.Image(
            src=opening_image_path,
            width=CONTENT_WIDTH,
            height=260,
            fit="contain",
            border_radius=24,
        )
        if os.path.exists(opening_image_path)
        else ft.Container(
            width=CONTENT_WIDTH,
            height=260,
            border_radius=24,
            bgcolor="#FFFFFF",
            alignment=ft.Alignment(0, 0),
            content=ft.Text("FINDY", size=34, weight=ft.FontWeight.BOLD, color=MAIN_COLOR),
        )
    )

    def go_login(e):
        router.go("login")
        rerender(page)

    body = ft.Column(
        controls=[
            ft.Container(height=12),
            hero_visual,
            ft.Container(height=SPACE_MD),
            hero_card(
                "Find Your Beauty",
                "나에게 어울리는 뷰티 아티스트와 예약 흐름을 한 번에 경험해보세요.",
                CONTENT_WIDTH,
                emoji="🪞",
            ),
            ft.Container(
                width=CONTENT_WIDTH,
                padding=ft.padding.symmetric(horizontal=4),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "뷰티 탐색부터 예약까지,\n더 부드럽고 더 직관적으로.",
                            size=25,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_STRONG,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            "스냅, 비디오, 아티스트 상세, 예약내역까지\n하나의 흐름으로 이어지는 FINDY 경험을 시작해보세요.",
                            size=13,
                            color=SUBTEXT_COLOR,
                        ),
                    ],
                    spacing=10,
                ),
            ),
            ft.Container(height=SPACE_MD),
            soft_button(
                "로그인 시작",
                MAIN_COLOR,
                "white",
                go_login,
                width=CONTENT_WIDTH,
                height=56,
            ),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
