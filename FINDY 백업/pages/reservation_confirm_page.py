import flet as ft

from components.cards import page_header, soft_button, browse_result_card, hero_card
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR, SUBTEXT_COLOR
from services.artist_service import find_artist_by_id
from services.reservation_service import save_reservation
from core import router
from .common import shell


def info_row(label, value):
    return ft.Row(
        controls=[
            ft.Text(label, size=12, color=SUBTEXT_COLOR),
            ft.Text(value, size=12, color="#1F1F1F", weight=ft.FontWeight.W_600),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        width=CONTENT_WIDTH,
    )


def render(page, app_state, rerender):
    form = app_state.get("reservation_form", {})
    artist = find_artist_by_id(form.get("artist_id"))

    if not artist:
        router.go_home()
        return rerender(page)

    def confirm(e):
        saved, error = save_reservation(app_state["reservation_history"], form)

        if error:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(error),
                bgcolor="#B85C5C",
            )
            page.snack_bar.open = True
            page.update()
            return

        app_state["last_completed_reservation"] = saved
        router.go_reservation_complete()
        rerender(page)

    hero = hero_card(
        "예약 확인",
        "선택한 내용을 마지막으로 확인하고 저장할 수 있어요.",
        CONTENT_WIDTH,
        emoji="✅",
    )

    artist_card = browse_result_card(
        {
            "title": artist["name"],
            "subtitle": artist["job"],
            "meta": f'{form.get("date")} · {form.get("time")}',
            "description": f'시술: {form.get("service")}\n요청사항: {form.get("note") or "없음"}',
            "badge": "예약",
        },
        CONTENT_WIDTH,
    )

    summary = ft.Container(
        width=CONTENT_WIDTH,
        padding=ft.padding.all(16),
        bgcolor="#FFFFFF",
        border_radius=24,
        border=ft.border.all(1, "#E7DED4"),
        content=ft.Column(
            controls=[
                info_row("아티스트", artist["name"]),
                info_row("직무", artist["job"]),
                info_row("시술", form.get("service") or "-"),
                info_row("날짜", form.get("date") or "-"),
                info_row("시간", form.get("time") or "-"),
                info_row("요청사항", form.get("note") or "없음"),
            ],
            spacing=10,
        ),
    )

    body = ft.Column(
        controls=[
            page_header(
                "예약 확인",
                on_back=lambda e: (router.go_reservation(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="확인 후 예약을 완료하면 내역에 바로 저장돼요.",
            ),
            hero,
            artist_card,
            summary,
            soft_button("예약 완료", MAIN_COLOR, "white", confirm, width=CONTENT_WIDTH, height=56),
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
