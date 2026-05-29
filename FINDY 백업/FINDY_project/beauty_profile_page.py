
import flet as ft
from components.cards import page_header, hero_card
from components.layout import CONTENT_WIDTH, SPACE_MD
from pages.common import shell
from core import router

def render(page, app_state, rerender):
    body = ft.Column(
        controls=[
            page_header(
                "나의 뷰티 정보",
                on_back=lambda e: (router.go_my(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="내 스타일과 선호를 관리해요.",
            ),
            hero_card(
                "뷰티 프로필",
                "선호 스타일, 피부 타입 등을 저장할 수 있어요.",
                CONTENT_WIDTH,
                emoji="🌿",
            ),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    shell(page, rerender, body, include_nav=False)
