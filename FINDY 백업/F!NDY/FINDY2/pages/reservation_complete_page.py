import flet as ft

from components.cards import page_header, soft_button, browse_result_card, hero_card
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR
from core import router
from .common import shell


def render(page, app_state, rerender):
    item = app_state.get("last_completed_reservation")

    if not item:
        router.go_home()
        return rerender(page)

    hero = hero_card(
        "예약 완료",
        "이제 예약내역에서 상태를 확인할 수 있어요.",
        CONTENT_WIDTH,
        emoji="🎉",
    )

    card = {
        "title": item.get("artist_name", "예약 완료"),
        "subtitle": item.get("job", ""),
        "meta": f'{item.get("date")} · {item.get("time")}',
        "description": f'시술: {item.get("service")}\n상태: {item.get("status")}',
        "badge": "완료",
    }

    body = ft.Column(
        controls=[
            page_header(
                "예약 완료",
                width=CONTENT_WIDTH,
                subtitle="브랜드 감성을 유지한 채 자연스럽게 예약이 저장되었어요.",
            ),
            hero,
            browse_result_card(card, CONTENT_WIDTH),
            soft_button(
                "예약내역 보기",
                MAIN_COLOR,
                "white",
                lambda e: (router.go_reservation_history(), rerender(page)),
                width=CONTENT_WIDTH,
                height=56,
            ),
            soft_button(
                "홈으로",
                "#FFFFFF",
                MAIN_COLOR,
                lambda e: (router.go_home(), rerender(page)),
                width=CONTENT_WIDTH,
                height=54,
            ),
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
