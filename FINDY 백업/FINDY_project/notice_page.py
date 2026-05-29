
import flet as ft
from components.cards import page_header, hero_card
from components.layout import CONTENT_WIDTH, SPACE_MD
from pages.common import shell
from core import router

def render(page, app_state, rerender):
    body = ft.Column(
        controls=[
            page_header(
                "공지사항",
                on_back=lambda e: (router.go_my(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="FINDY의 새로운 소식을 확인하세요.",
            ),
            hero_card(
                "공지",
                "업데이트와 이벤트가 표시될 예정이에요.",
                CONTENT_WIDTH,
                emoji="📢",
            ),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    shell(page, rerender, body, include_nav=False)
