import flet as ft
from datetime import date, timedelta

from components.cards import page_header, soft_button, chip, hero_card, section_title
from components.layout import (
    CONTENT_WIDTH,
    SPACE_MD,
    SPACE_LG,
    MAIN_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
    BORDER_COLOR,
)
from services.artist_service import find_artist_by_id, get_artist_schedule, get_artist_services
from core import router
from .common import shell


def info_tile(title, value):
    return ft.Container(
        expand=True,
        padding=ft.padding.all(16),
        bgcolor="#FFFFFF",
        border_radius=22,
        border=ft.border.all(1, "#E7DED4"),
        content=ft.Column(
            controls=[
                ft.Text(title, size=11, color=SUBTEXT_COLOR),
                ft.Text(value, size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ],
            spacing=5,
        ),
    )


def render(page, app_state, rerender):
    form = app_state.get("reservation_form", {})
    artist = find_artist_by_id(form.get("artist_id"))

    if not artist:
        router.go_home()
        return rerender(page)

    schedule = get_artist_schedule(artist)
    services = get_artist_services(artist)
    days = [(date.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    slots = []
    hour = int(schedule["start"].split(":")[0])
    end_hour = int(schedule["end"].split(":")[0])

    for h in range(hour, end_hour + 1):
        for m in ["00", "30"]:
            slots.append(f"{h:02d}:{m}")

    note_field = ft.TextField(
        width=CONTENT_WIDTH,
        value=form.get("note", ""),
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_radius=16,
        bgcolor="#FFFFFF",
        border_color=BORDER_COLOR,
        focused_border_color=MAIN_COLOR,
        cursor_color=MAIN_COLOR,
        hint_text="요청사항이 있으면 적어주세요.",
        content_padding=16,
        on_change=lambda e: form.__setitem__("note", e.control.value or ""),
    )

    service_row = ft.Row(
        controls=[
            chip(
                s,
                selected=(form.get("service") == s),
                on_click=lambda e, value=s: (
                    form.__setitem__("service", value),
                    rerender(page),
                ),
            )
            for s in services
        ],
        wrap=True,
        spacing=8,
        run_spacing=8,
        width=CONTENT_WIDTH,
    )

    date_row = ft.Row(
        controls=[
            chip(
                d[5:],
                selected=(form.get("date") == d),
                on_click=lambda e, value=d: (
                    form.__setitem__("date", value),
                    form.__setitem__("time", None),
                    rerender(page),
                ),
            )
            for d in days
        ],
        wrap=True,
        spacing=8,
        run_spacing=8,
        width=CONTENT_WIDTH,
    )

    time_row = ft.Row(
        controls=[
            chip(
                t,
                selected=(form.get("time") == t),
                on_click=lambda e, value=t: (
                    form.__setitem__("time", value),
                    rerender(page),
                ),
            )
            for t in slots[:18]
        ],
        wrap=True,
        spacing=8,
        run_spacing=8,
        width=CONTENT_WIDTH,
    )

    def go_next(e):
        if not form.get("service") or not form.get("date") or not form.get("time"):
            page.snack_bar = ft.SnackBar(
                content=ft.Text("시술, 날짜, 시간을 선택해주세요."),
                bgcolor="#B85C5C",
            )
            page.snack_bar.open = True
            page.update()
            return

        router.go_reservation_confirm()
        rerender(page)

    hero = hero_card(
        "예약하기",
        f'{artist["name"]} · {artist["job"]}',
        CONTENT_WIDTH,
        emoji="🗓️",
    )

    top_info = ft.Row(
        controls=[
            info_tile("예약 가능 시간", f'{schedule["start"]} - {schedule["end"]}'),
            ft.Container(width=10),
            info_tile("대표 카테고리", artist["category"]),
        ],
        width=CONTENT_WIDTH,
        spacing=0,
    )

    summary = ft.Container(
        width=CONTENT_WIDTH,
        padding=16,
        bgcolor="#FFFFFF",
        border_radius=24,
        border=ft.border.all(1, "#E7DED4"),
        content=ft.Column(
            controls=[
                ft.Text("예약 요약", size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text(f'시술: {form.get("service") or "선택 전"}', size=12, color=SUBTEXT_COLOR),
                ft.Text(f'날짜: {form.get("date") or "선택 전"}', size=12, color=SUBTEXT_COLOR),
                ft.Text(f'시간: {form.get("time") or "선택 전"}', size=12, color=SUBTEXT_COLOR),
                ft.Text(f'요청사항: {form.get("note") or "없음"}', size=12, color=SUBTEXT_COLOR),
            ],
            spacing=5,
        ),
    )

    body = ft.Column(
        controls=[
            page_header(
                "예약",
                on_back=lambda e: (router.go_detail(artist["id"]), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="시술, 날짜, 시간을 선택하고 부드럽게 다음 단계로 이동할 수 있어요.",
            ),
            hero,
            top_info,
            section_title("시술 선택", "원하는 서비스를 먼저 골라주세요.", width=CONTENT_WIDTH),
            service_row,
            section_title("날짜 선택", "가까운 일정부터 편하게 선택할 수 있어요.", width=CONTENT_WIDTH),
            date_row,
            section_title("시간 선택", "가능한 시간대를 카드형 칩으로 정리했어요.", width=CONTENT_WIDTH),
            time_row,
            section_title("요청사항", "원하는 스타일이나 참고사항을 남겨보세요.", width=CONTENT_WIDTH),
            note_field,
            summary,
            soft_button(
                "예약 확인",
                MAIN_COLOR,
                "white",
                go_next,
                width=CONTENT_WIDTH,
                height=56,
            ),
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
