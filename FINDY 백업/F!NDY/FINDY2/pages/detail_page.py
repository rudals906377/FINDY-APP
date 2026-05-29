import flet as ft

from components.cards import page_header, soft_button, browse_result_card, chip, hero_card, section_title
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR, TEXT_COLOR
from services.artist_service import find_artist_by_id, get_artist_services
from core import router
from .common import shell


def render(page, app_state, rerender):
    artist = find_artist_by_id(app_state.get("detail_artist_id"))

    if not artist:
        router.go_home()
        return rerender(page)

    def start_reservation(e):
        app_state["reservation_form"] = {
            "artist_id": artist["id"],
            "artist_name": artist["name"],
            "job": artist["job"],
            "category": artist["category"],
            "service": get_artist_services(artist)[0] if get_artist_services(artist) else "",
            "date": None,
            "time": None,
            "note": "",
        }
        router.go_reservation()
        rerender(page)

    services = get_artist_services(artist)

    service_row = ft.Row(
        controls=[chip(label) for label in services[:6]],
        wrap=True,
        spacing=8,
        run_spacing=8,
        width=CONTENT_WIDTH,
    )

    mood_row = ft.Row(
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.all(16),
                bgcolor="#FFFFFF",
                border_radius=22,
                border=ft.border.all(1, "#E7DED4"),
                content=ft.Column(
                    controls=[
                        ft.Text("스타일", size=14, weight=ft.FontWeight.BOLD, color="#1F1F1F"),
                        ft.Text(artist["style"], size=12, color="#8A8178"),
                    ],
                    spacing=6,
                ),
            ),
            ft.Container(width=10),
            ft.Container(
                expand=True,
                padding=ft.padding.all(16),
                bgcolor="#FFFFFF",
                border_radius=22,
                border=ft.border.all(1, "#E7DED4"),
                content=ft.Column(
                    controls=[
                        ft.Text("추천 이유", size=14, weight=ft.FontWeight.BOLD, color="#1F1F1F"),
                        ft.Text(artist["reason"], size=12, color="#8A8178"),
                    ],
                    spacing=6,
                ),
            ),
        ],
        width=CONTENT_WIDTH,
        spacing=0,
    )

    hero = hero_card(
        artist["name"],
        f'{artist["job"]} · {artist["category"]}',
        CONTENT_WIDTH,
        emoji="💄" if artist["category"] == "메이크업" else "✂️" if artist["category"] == "헤어" else "📸",
    )

    profile_card = browse_result_card(
        {
            "title": artist["name"],
            "subtitle": artist["job"],
            "meta": f'⭐ {artist["rating"]} · {artist["distance"]} · {artist["price"]}',
            "description": artist["intro"],
            "badge": artist["category"],
        },
        CONTENT_WIDTH,
    )

    body = ft.Column(
        controls=[
            page_header(
                "아티스트",
                on_back=lambda e: (router.go_home(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="상세 정보를 보고 바로 예약으로 이어질 수 있어요.",
            ),
            hero,
            profile_card,
            mood_row,
            section_title(
                "대표 서비스",
                "선호하는 시술 흐름을 빠르게 확인해보세요.",
                width=CONTENT_WIDTH,
            ),
            service_row,
            soft_button(
                "예약하기",
                MAIN_COLOR,
                "white",
                start_reservation,
                width=CONTENT_WIDTH,
                height=56,
            ),
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
