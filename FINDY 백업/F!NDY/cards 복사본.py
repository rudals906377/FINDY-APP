import flet as ft
from components.layout import (
    BG_COLOR,
    BORDER_COLOR,
    CARD_COLOR,
    CARD_SHADOW,
    CHIP_BG,
    MAIN_COLOR,
    MAIN_COLOR_SOFT,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_XL,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SUBTEXT_COLOR,
    TEXT_COLOR,
)


def _shadow(token):
    return ft.BoxShadow(
        spread_radius=token["spread_radius"],
        blur_radius=token["blur_radius"],
        color=token["color"],
        offset=ft.Offset(token["offset_x"], token["offset_y"]),
    )



def page_header(title, on_back=None, width=None):
    leading = (
        ft.Container(
            width=40,
            height=40,
            border_radius=999,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, BORDER_COLOR),
            alignment=ft.Alignment(0, 0),
            on_click=on_back,
            ink=True,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color="#0D000000", offset=ft.Offset(0, 3)),
            content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, size=16, color=TEXT_COLOR),
        )
        if on_back
        else ft.Container(width=40, height=40)
    )

    return ft.Container(
        width=width,
        padding=ft.padding.only(left=2, right=2, top=2, bottom=2),
        content=ft.Row(
            controls=[
                leading,
                ft.Container(
                    expand=True,
                    content=ft.Text(title, size=24, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                ),
            ],
            spacing=SPACE_MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )



def section_title(title, subtitle=None, on_click=None, width=None):
    title_block = ft.Column(
        controls=[
            ft.Text(title, size=20, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
            ft.Text(subtitle, size=11, color=SUBTEXT_COLOR) if subtitle else ft.Container(),
        ],
        spacing=4,
    )

    trailing = (
        ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=999,
            bgcolor=MAIN_COLOR_SOFT,
            content=ft.Row(
                controls=[
                    ft.Text("전체보기", size=11, color=MAIN_COLOR, weight=ft.FontWeight.W_600),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=11, color=MAIN_COLOR),
                ],
                spacing=4,
                tight=True,
            ),
        )
        if on_click
        else None
    )

    return ft.Container(
        width=width,
        padding=ft.padding.only(left=2, right=2, top=2, bottom=4),
        on_click=on_click,
        ink=on_click is not None,
        content=ft.Row(
            controls=[title_block, trailing or ft.Container()],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )



def soft_button(label, bgcolor, text_color, on_click, border=None, width=300):
    resolved_bg = bgcolor if bgcolor != CARD_COLOR else "#FFFFFF"
    return ft.Container(
        width=width,
        height=54,
        bgcolor=resolved_bg,
        border_radius=18,
        border=border or ft.border.all(1, BORDER_COLOR),
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=14, color="#14000000", offset=ft.Offset(0, 5)),
        gradient=(
            ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[resolved_bg, resolved_bg],
            )
            if resolved_bg != "#FFFFFF"
            else None
        ),
        content=ft.Row(
            controls=[ft.Text(label, color=text_color, size=15, weight=ft.FontWeight.W_700)],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )



def _chip(label):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        bgcolor=CHIP_BG,
        border_radius=999,
        border=ft.border.all(1, BORDER_COLOR),
        content=ft.Text(label, size=10, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
    )



def review_card(name, category, review, width):
    return ft.Container(
        width=width,
        padding=ft.padding.symmetric(horizontal=16, vertical=16),
        bgcolor="#FFFFFF",
        border_radius=RADIUS_LG,
        border=ft.border.all(1, BORDER_COLOR),
        shadow=_shadow(CARD_SHADOW),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(name, size=15, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                                ft.Text("실사용 후기", size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        _chip(category),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    controls=[
                        ft.Text("★★★★★", size=12, color=MAIN_COLOR),
                        ft.Text("검증된 리뷰", size=11, color=SUBTEXT_COLOR),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(
                    padding=ft.padding.all(12),
                    bgcolor=BG_COLOR,
                    border_radius=RADIUS_MD,
                    content=ft.Text(review, size=13, color=SUBTEXT_COLOR, height=1.35),
                ),
            ],
            spacing=10,
        ),
    )



def browse_result_card(item, width):
    badge = item.get("badge", "목록")
    meta = item.get("meta", "")
    description = item.get("description", "")

    return ft.Container(
        width=width,
        padding=ft.padding.symmetric(horizontal=18, vertical=18),
        bgcolor="#FFFFFF",
        border_radius=RADIUS_XL,
        border=ft.border.all(1, BORDER_COLOR),
        shadow=_shadow(CARD_SHADOW),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Column(
                                controls=[
                                    ft.Text(item.get("title", ""), size=17, weight=ft.FontWeight.W_700, color=TEXT_COLOR),
                                    ft.Text(item.get("subtitle", ""), size=12, color=SUBTEXT_COLOR),
                                ],
                                spacing=5,
                            ),
                        ),
                        _chip(badge),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    bgcolor=MAIN_COLOR_SOFT,
                    border_radius=RADIUS_MD,
                    content=ft.Text(meta, size=12, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                ) if meta else ft.Container(),
                ft.Text(description, size=13, color=SUBTEXT_COLOR, height=1.35),
            ],
            spacing=10,
        ),
    )
