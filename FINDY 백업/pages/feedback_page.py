
import flet as ft
from components.cards import page_header, soft_button
from components.layout import CONTENT_WIDTH, SPACE_MD
from pages.common import shell
from core import router

def render(page, app_state, rerender):
    feedback_text = ft.TextField(
        width=CONTENT_WIDTH,
        multiline=True,
        min_lines=4,
        hint_text="불편한 점이나 개선 아이디어를 자유롭게 적어주세요.",
    )

    def submit(e):
        feedback_text.value = ""
        page.snack_bar = ft.SnackBar(ft.Text("의견이 전달되었어요 👍"))
        page.snack_bar.open = True
        page.update()

    body = ft.Column(
        controls=[
            page_header(
                "개선 의견",
                on_back=lambda e: (router.go_my(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="서비스 개선을 도와주세요.",
            ),
            feedback_text,
            soft_button("의견 보내기", "#000000", "white", submit),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
