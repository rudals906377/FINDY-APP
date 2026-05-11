
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
        border=ft.border.all(1, "#ECE5DB"),
        content=ft.Column(
            controls=[
                ft.Text(title, size=12, color="#8A8178"),
                ft.Text(value, size=18, weight=ft.FontWeight.W_500, color="#1F1F1F"),
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
            "title": "완료한 시술",
            "subtitle": "완료된 시술 및 방문 기록",
            "meta": "바로가기",
            "description": "지금까지 완료된 시술 흐름을 확인할 수 있어요.",
            "badge": "DONE",
            "on_click": lambda e: (router.go_completed(), rerender(page)),
        },
        {
            "title": "나의 뷰티 정보",
            "subtitle": "스타일과 선호 관리",
            "meta": "바로가기",
            "description": "내 취향과 뷰티 프로필을 확인하고 관리할 수 있어요.",
            "badge": "INFO",
            "on_click": lambda e: (router.go_beauty_profile(), rerender(page)),
        },
        {
            "title": "공지사항",
            "subtitle": "서비스 업데이트와 소식",
            "meta": "바로가기",
            "description": "FINDY의 새로운 공지와 운영 소식을 확인할 수 있어요.",
            "badge": "NOTICE",
            "on_click": lambda e: (router.go_notice(), rerender(page)),
        },
        {
            "title": "개선 의견",
            "subtitle": "불편한 점과 아이디어 전달",
            "meta": "바로가기",
            "description": "서비스 개선을 위한 의견을 자유롭게 남길 수 있어요.",
            "badge": "FEED",
            "on_click": lambda e: (router.go_feedback(), rerender(page)),
        },
        {
            "title": "고객센터",
            "subtitle": "도움이 필요할 때",
            "meta": "바로가기",
            "description": "운영시간, 자주 묻는 질문, 1:1 문의로 연결돼요.",
            "badge": "HELP",
            "on_click": lambda e: (router.go_support(), rerender(page)),
        },
        {
            "title": "문의내역",
            "subtitle": "내가 남긴 문의 확인",
            "meta": f'{len(app_state.get("inquiry_history", []))}건' if app_state.get("inquiry_history") else "바로가기",
            "description": "접수한 문의 내용을 확인하고 새 문의를 남길 수 있어요.",
            "badge": "QNA",
            "on_click": lambda e: (router.go_inquiry(), rerender(page)),
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
