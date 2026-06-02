import flet as ft

from components.cards import page_header, section_title, hero_card, chip, review_card
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR, MAIN_COLOR_SOFT, SUBTEXT_COLOR, TEXT_COLOR, BORDER_COLOR
from data.reviews import REVIEW_ITEMS
from .common import shell


def _category_emoji(name: str) -> str:
    mapping = {
        "전체": "✨",
        "헤어": "✂️",
        "메이크업": "💄",
        "네일아트": "💅",
        "포토": "📸",
        "웨딩": "💍",
        "반영구시술": "🪄",
    }
    return mapping.get(name, "✨")


def render(page, app_state, rerender):
    selected_category = app_state.get("home_filter", "전체")
    all_categories = ["전체", "헤어", "메이크업", "네일아트", "포토", "웨딩", "반영구시술"]

    featured_reviews = REVIEW_ITEMS[:3]

    def set_filter(category_name: str):
        app_state["home_filter"] = category_name
        rerender(page)

    category_row = ft.Row(
        controls=[
            chip(
                f"{_category_emoji(name)} {name}",
                selected=(selected_category == name),
                on_click=lambda e, value=name: set_filter(value),
            )
            for name in all_categories
        ],
        wrap=True,
        spacing=8,
        run_spacing=8,
        width=CONTENT_WIDTH,
    )

    hero_banner = ft.Container(
        width=CONTENT_WIDTH,
        padding=ft.padding.all(18),
        bgcolor="#FFFFFF",
        border_radius=28,
        border=ft.border.all(1, BORDER_COLOR),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            bgcolor=MAIN_COLOR_SOFT,
                            border_radius=12,
                            content=ft.Text("오늘의 추천", size=10, weight=ft.FontWeight.W_500, color=MAIN_COLOR),
                        ),
                    ]
                ),
                ft.Text("지금 어울리는 뷰티 아티스트를 바로 찾아보세요", size=22, weight=ft.FontWeight.W_500, color=TEXT_COLOR),
                ft.Text(
                    "카테고리별 추천과 실제 리뷰, 스냅 무드를 한 화면에서 보고 바로 상세로 넘어갈 수 있어요.",
                    size=12,
                    color=SUBTEXT_COLOR,
                ),
                ft.Container(
                    expand=True,
                    padding=ft.padding.all(14),
                    bgcolor="#FFFFFF",
                    border_radius=20,
                    content=ft.Column(
                        controls=[
                            ft.Text("선택 카테고리", size=11, color=SUBTEXT_COLOR),
                            ft.Text(selected_category, size=18, weight=ft.FontWeight.W_500, color=TEXT_COLOR),
                        ],
                        spacing=4,
                    ),
                ),
            ],
            spacing=12,
        ),
    )

    review_cards = [
        review_card(name, category, review, CONTENT_WIDTH)
        for name, category, review in featured_reviews
    ]

    body = ft.Column(
        controls=[
            page_header(
                "홈",
                width=CONTENT_WIDTH,
                subtitle="추천 아티스트와 무드를 빠르게 둘러볼 수 있어요.",
            ),
            hero_card(
                "FINDY 홈",
                "탐색부터 예약까지 자연스럽게 이어지는 오늘의 추천 흐름이에요.",
                CONTENT_WIDTH,
                emoji="🏠",
            ),
            hero_banner,
            section_title("카테고리 둘러보기", "원하는 스타일을 먼저 고르면 추천이 더 빨라져요.", width=CONTENT_WIDTH),
            category_row,
            section_title("실제 리뷰", "사용자들이 많이 언급한 만족 포인트예요.", width=CONTENT_WIDTH),
            *review_cards,
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=True)
