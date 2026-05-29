import flet as ft

from components.cards import page_header, section_title, browse_result_card, soft_button, hero_card
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, SUBTEXT_COLOR
from services.reservation_service import classify_history_item, cancel_reservation
from core import router
from .common import shell


def reservation_card(item, page, app_state, rerender):
    kind = classify_history_item(item)

    if kind == "cancelled":
        badge = "취소된 예약"
    elif kind == "past":
        badge = "지난 예약"
    else:
        badge = "다가오는 예약"

    card = browse_result_card(
        {
            "title": item.get("artist_name", ""),
            "subtitle": item.get("job", ""),
            "meta": f'{item.get("date")} · {item.get("time")}',
            "description": f'시술: {item.get("service")}\n상태: {item.get("status")}',
            "badge": badge,
        },
        CONTENT_WIDTH,
    )

    controls = [card]

    if item.get("status") == "예약 완료" and kind == "upcoming":
        controls.append(
            soft_button(
                "예약 취소",
                "#FFF3F0",
                "#B85C5C",
                lambda e, rid=item.get("id"): (_cancel(page, app_state, rerender, rid)),
                width=CONTENT_WIDTH,
                height=52,
                border=ft.border.all(1, "#F2D2CC"),
            )
        )

    return ft.Column(controls=controls, spacing=8)


def _cancel(page, app_state, rerender, reservation_id):
    cancel_reservation(app_state["reservation_history"], reservation_id)
    rerender(page)


def empty_card(message):
    return ft.Container(
        width=CONTENT_WIDTH,
        padding=ft.padding.all(18),
        bgcolor="#FFFFFF",
        border_radius=24,
        border=ft.border.all(1, "#E6D7C8"),
        content=ft.Text(message, size=12, color=SUBTEXT_COLOR),
    )


def render(page, app_state, rerender):
    history = list(reversed(app_state.get("reservation_history", [])))

    upcoming = [item for item in history if classify_history_item(item) == "upcoming"]
    past = [item for item in history if classify_history_item(item) == "past"]
    cancelled = [item for item in history if classify_history_item(item) == "cancelled"]

    hero = hero_card(
        "예약내역",
        "다가오는 일정부터 지난 예약, 취소 내역까지 한눈에 볼 수 있어요.",
        CONTENT_WIDTH,
        emoji="🗂️",
    )

    body_controls = [
        page_header(
            "예약내역",
            on_back=lambda e: (router.go_my(), rerender(page)),
            width=CONTENT_WIDTH,
            subtitle="브랜드 톤을 유지한 채 예약 상태를 더 편하게 관리할 수 있어요.",
        ),
        hero,
        section_title("다가오는 예약", "변경이 필요하면 여기서 취소할 수 있어요.", width=CONTENT_WIDTH),
    ]

    if upcoming:
        for item in upcoming:
            body_controls.append(reservation_card(item, page, app_state, rerender))
    else:
        body_controls.append(empty_card("예정된 예약이 없어요."))

    body_controls.append(
        section_title("지난 예약", "방문이 끝났거나 시간이 지난 예약이에요.", width=CONTENT_WIDTH)
    )

    if past:
        for item in past:
            body_controls.append(reservation_card(item, page, app_state, rerender))
    else:
        body_controls.append(empty_card("지난 예약이 아직 없어요."))

    body_controls.append(
        section_title("취소된 예약", "취소된 예약도 기록으로 남겨둘게요.", width=CONTENT_WIDTH)
    )

    if cancelled:
        for item in cancelled:
            body_controls.append(reservation_card(item, page, app_state, rerender))
    else:
        body_controls.append(empty_card("취소된 예약이 없어요."))

    body_controls.append(ft.Container(height=SPACE_LG))

    body = ft.Column(
        controls=body_controls,
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=True)
