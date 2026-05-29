
import flet as ft
from components.cards import page_header, hero_card
from components.layout import CONTENT_WIDTH, SPACE_MD
from pages.common import shell
from core import router

def render(page, app_state, rerender):
    body = ft.Column(
        controls=[
            page_header(
                "완료한 시술",
                on_back=lambda e: (router.go_my(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="지금까지 받은 시술 기록이에요.",
            ),
            hero_card(
                "시술 기록",
                "완료된 예약 내역을 기반으로 보여줄 예정이에요.",
                CONTENT_WIDTH,
                emoji="✔️",
            ),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    shell(page, rerender, body, include_nav=False)
