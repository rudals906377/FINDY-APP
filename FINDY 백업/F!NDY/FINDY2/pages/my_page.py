import flet as ft

from components.cards import page_header, hero_card, browse_result_card
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG
from core import router
from .common import shell


def info_tile(title, value, subtitle=""):
    return ft.Container(
        expand=True,
        padding=ft.padding.all(16),
        bgcolor="#FFFFFF",
        border_radius=22,
        border=ft.border.all(1, "#E7DED4"),
        content=ft.Column(
            controls=[
                ft.Text(title, size=12, color="#8A8178"),
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color="#1F1F1F"),
                ft.Text(subtitle, size=10, color="#B1A79D") if subtitle else ft.Container(height=0),
            ],
            spacing=5,
        ),
    )


def render(page, app_state, rerender):
    saved_count = len(app_state.get("saved_ids", set()))
    reservation_count = len(app_state.get("reservation_history", []))

    hero = hero_card(
        "내정보",
        "예약, 저장한 뷰티, 개인화된 흐름을 한 곳에서 관리할 수 있어요.",
        CONTENT_WIDTH,
        emoji="👤",
    )

    stats_row = ft.Row(
        controls=[
            info_tile("예약", str(reservation_count), "현재 저장된 예약"),
            ft.Container(width=10),
            info_tile("저장", str(saved_count), "찜한 아티스트"),
        ],
        width=CONTENT_WIDTH,
        spacing=0,
    )

    menu_cards = [
        {
            "title": "예약내역",
            "subtitle": "다가오는 예약과 지난 예약",
            "meta": "바로가기",
            "description": "예약 상태를 확인하고 필요한 경우 취소할 수 있어요.",
            "badge": "MY",
            "on_click": lambda e: (router.go_reservation_history(), rerender(page)),
        },
        {
            "title": "저장한 뷰티",
            "subtitle": "관심 있는 아티스트와 스타일",
            "meta": "준비 중",
            "description": "찜 기능을 연결하면 여기에 모아서 볼 수 있어요.",
            "badge": "SAVE",
            "on_click": None,
        },
        {
            "title": "계정 및 설정",
            "subtitle": "알림, 개인 설정, 앱 정보",
            "meta": "준비 중",
            "description": "이후 설정 화면과 연결될 예정이에요.",
            "badge": "SET",
            "on_click": None,
        },
    ]

    cards = [
        browse_result_card(item, CONTENT_WIDTH, on_click=item["on_click"])
        for item in menu_cards
    ]

    body = ft.Column(
        controls=[
            page_header(
                "내정보",
                width=CONTENT_WIDTH,
                subtitle="브랜드 톤을 유지한 채 개인화된 정보를 정리해두었어요.",
            ),
            hero,
            stats_row,
            *cards,
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=True)
