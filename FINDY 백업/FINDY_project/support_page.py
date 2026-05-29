import flet as ft

from components.cards import page_header, hero_card, browse_result_card, soft_button, section_title
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR, SUBTEXT_COLOR
from core import router
from .common import shell


FAQ_ITEMS = [
    {
        "title": "예약은 어떻게 진행되나요?",
        "subtitle": "가장 자주 묻는 질문",
        "meta": "예약 안내",
        "description": "홈에서 아티스트를 선택한 뒤 예약 페이지에서 날짜와 시간을 고르면 바로 예약을 완료할 수 있어요.",
        "badge": "FAQ",
    },
    {
        "title": "예약을 취소하고 싶어요",
        "subtitle": "예약내역에서 바로 가능",
        "meta": "취소 안내",
        "description": "내정보 > 예약내역에서 다가오는 예약을 확인한 뒤 취소 버튼으로 바로 취소할 수 있어요.",
        "badge": "FAQ",
    },
    {
        "title": "찜한 아티스트는 어디서 보나요?",
        "subtitle": "저장 기능 안내",
        "meta": "저장 기능",
        "description": "저장한 아티스트 기능은 현재 확장 중이며, 우선은 홈과 상세 화면 중심으로 탐색할 수 있어요.",
        "badge": "FAQ",
    },
]



def _info_block(title: str, value: str, subtitle: str = ""):
    return ft.Container(
        expand=True,
        padding=ft.padding.all(16),
        bgcolor="#FFFFFF",
        border_radius=22,
        border=ft.border.all(1, "#ECE5DB"),
        content=ft.Column(
            controls=[
                ft.Text(title, size=11, color=SUBTEXT_COLOR),
                ft.Text(value, size=15, weight=ft.FontWeight.W_500, color="#1F1F1F"),
                ft.Text(subtitle, size=10, color="#B1A79D") if subtitle else ft.Container(height=0),
            ],
            spacing=5,
        ),
    )



def render(page, app_state, rerender):
    faq_cards = [browse_result_card(item, CONTENT_WIDTH) for item in FAQ_ITEMS]

    body = ft.Column(
        controls=[
            page_header(
                "고객센터",
                on_back=lambda e: (router.go_my(), rerender(page)),
                width=CONTENT_WIDTH,
                subtitle="자주 묻는 질문과 문의하기를 한곳에서 확인할 수 있어요.",
            ),
            hero_card(
                "도움이 필요하신가요?",
                "빠르게 확인할 수 있는 안내와 문의 접수를 준비했어요.",
                CONTENT_WIDTH,
                emoji="🎧",
            ),
            ft.Row(
                controls=[
                    _info_block("운영시간", "평일 10:00 - 18:00", "주말 및 공휴일 제외"),
                    ft.Container(width=10),
                    _info_block("답변 기준", "24시간 이내", "순차적으로 답변드려요"),
                ],
                width=CONTENT_WIDTH,
                spacing=0,
            ),
            soft_button(
                "1:1 문의하기",
                MAIN_COLOR,
                "white",
                lambda e: (router.go_inquiry(), rerender(page)),
                width=CONTENT_WIDTH,
                height=56,
            ),
            section_title("자주 묻는 질문", "먼저 확인하면 더 빠르게 해결할 수 있어요.", width=CONTENT_WIDTH),
            *faq_cards,
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
