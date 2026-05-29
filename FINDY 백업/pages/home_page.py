import flet as ft

from components.cards import page_header, section_title, browse_result_card, hero_card, chip, review_card, soft_button
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR, MAIN_COLOR_SOFT, SUBTEXT_COLOR, TEXT_COLOR, BORDER_COLOR
from services.artist_service import list_artists
from data.reviews import REVIEW_ITEMS
from data.snaps import SNAP_ITEMS
from core import router
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


def _artist_card_item(artist):
    tags = " · ".join(artist.get("tags", [])[:2])
    tag_text = f"추천 키워드: {tags}" if tags else artist.get("intro", "")
    return {
        "title": artist.get("name", ""),
        "subtitle": artist.get("job", ""),
        "meta": f"⭐ {artist.get('rating', '-') } · {artist.get('distance', '-') } · {artist.get('price', '-') }",
        "description": f"{artist.get('intro', '')}\n{tag_text}",
        "badge": artist.get("category", "추천"),
    }


def _open_detail(page, rerender, artist_id: str):
    router.go_detail(artist_id)
    rerender(page)


def render(page, app_state, rerender):
    selected_category = app_state.get("home_filter", "전체")
    all_categories = ["전체", "헤어", "메이크업", "네일아트", "포토", "웨딩", "반영구시술"]

    artists = list_artists(None if selected_category == "전체" else selected_category)
    featured_artists = artists[:4] if artists else list_artists()[:4]
    trending_snaps = SNAP_ITEMS[:3]
    featured_reviews = REVIEW_ITEMS[:3]

    def set_filter(category_name: str):
        app_state["home_filter"] = category_name
        rerender(page)

    def go_snap(e):
        router.go_snap()
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
                            content=ft.Text("오늘의 추천", size=10, weight=ft.FontWeight.W_600, color=MAIN_COLOR),
                        ),
                    ]
                ),
                ft.Text("지금 어울리는 뷰티 아티스트를 바로 찾아보세요", size=22, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text(
                    "카테고리별 추천과 실제 후기, 스냅 무드를 한 화면에서 보고 바로 상세로 넘어갈 수 있어요.",
                    size=12,
                    color=SUBTEXT_COLOR,
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            expand=True,
                            padding=ft.padding.all(14),
                            bgcolor="#FCFAF7",
                            border_radius=20,
                            content=ft.Column(
                                controls=[
                                    ft.Text("추천 수", size=11, color=SUBTEXT_COLOR),
                                    ft.Text(f"{len(featured_artists)}명", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ],
                                spacing=4,
                            ),
                        ),
                        ft.Container(width=10),
                        ft.Container(
                            expand=True,
                            padding=ft.padding.all(14),
                            bgcolor="#FCFAF7",
                            border_radius=20,
                            content=ft.Column(
                                controls=[
                                    ft.Text("선택 카테고리", size=11, color=SUBTEXT_COLOR),
                                    ft.Text(selected_category, size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ],
                                spacing=4,
                            ),
                        ),
                    ],
                    spacing=0,
                    width=CONTENT_WIDTH,
                ),
            ],
            spacing=12,
        ),
    )

    featured_cards = [
        browse_result_card(
            _artist_card_item(artist),
            CONTENT_WIDTH,
            on_click=lambda e, artist_id=artist["id"]: _open_detail(page, rerender, artist_id),
        )
        for artist in featured_artists
    ]

    snap_preview = ft.Row(
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.all(14),
                bgcolor="#FFFFFF",
                border_radius=22,
                border=ft.border.all(1, BORDER_COLOR),
                content=ft.Column(
                    controls=[
                        ft.Text(emoji, size=22),
                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(subtitle, size=11, color=SUBTEXT_COLOR),
                    ],
                    spacing=6,
                ),
            )
            for title, subtitle, emoji in trending_snaps
        ],
        spacing=10,
        width=CONTENT_WIDTH,
    )

    review_cards = [
        review_card(name, category, review, CONTENT_WIDTH)
        for name, category, review in featured_reviews
    ]

    featured_section_controls = featured_cards if featured_cards else [
        ft.Container(
            width=CONTENT_WIDTH,
            padding=ft.padding.all(18),
            bgcolor="#FFFFFF",
            border_radius=24,
            border=ft.border.all(1, BORDER_COLOR),
            content=ft.Text("선택한 카테고리에 해당하는 아티스트가 아직 없어요.", size=12, color=SUBTEXT_COLOR),
        )
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
            section_title("지금 추천 아티스트", "카드를 누르면 바로 상세 페이지로 이동해요.", width=CONTENT_WIDTH),
            *featured_section_controls,
            section_title("스냅 무드 미리보기", "요즘 많이 찾는 촬영 무드를 간단히 모아봤어요.", on_click=go_snap, width=CONTENT_WIDTH),
            snap_preview,
            section_title("실제 후기", "사용자들이 많이 언급한 만족 포인트예요.", width=CONTENT_WIDTH),
            *review_cards,
            soft_button(
                "스냅 더 보기",
                "#FFFFFF",
                MAIN_COLOR,
                go_snap,
                width=CONTENT_WIDTH,
                height=54,
            ),
            ft.Container(height=SPACE_LG),
        ],
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=True)
