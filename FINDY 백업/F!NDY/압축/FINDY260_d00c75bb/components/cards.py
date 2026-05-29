import flet as ft
from components.layout import CARD_COLOR, CHIP_BG, MAIN_COLOR, SPACE_MD, SPACE_LG, RADIUS_XL, SUBTEXT_COLOR, TEXT_COLOR

def page_header(title, on_back=None, width=None):
    return ft.Container(
        width=width,
        content=ft.Row(
            controls=[
                ft.Container(
                    width=34,
                    height=34,
                    border_radius=999,
                    alignment=ft.Alignment(0, 0),
                    on_click=on_back,
                    ink=True,
                    content=ft.Text("<", size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ) if on_back else ft.Container(width=34, height=34),
                ft.Text(title, size=23, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ],
            spacing=SPACE_MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

def section_title(title, subtitle=None, on_click=None, width=None):
    controls = [ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)]
    if subtitle:
        controls.append(ft.Text(subtitle, size=10, color=SUBTEXT_COLOR))
    return ft.Container(
        width=width,
        padding=ft.padding.only(left=2, right=2),
        on_click=on_click,
        ink=on_click is not None,
        content=ft.Column(expand=True, controls=controls, spacing=3),
    )

def soft_button(label, bgcolor, text_color, on_click, border=None, width=300):
    return ft.Container(
        width=width,
        height=52,
        bgcolor=bgcolor if bgcolor != CARD_COLOR else ft.Colors.with_opacity(0.72, "#FFFFFF"),
        border_radius=0,
        border=border or ft.border.all(1, ft.Colors.with_opacity(0.42, "#FFFFFF")),
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=14, color="#14000000", offset=ft.Offset(0, 4)),
        content=ft.Row(
            controls=[ft.Text(label, color=text_color, size=15, weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

def review_card(name, category, review, width):
    return ft.Container(
        width=width,
        padding=SPACE_MD,
        bgcolor=ft.Colors.with_opacity(0.84, "#FFFFFF"),
        border_radius=22,
        border=ft.border.all(1, ft.Colors.with_opacity(0.45, "#FFFFFF")),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=18, color="#16000000", offset=ft.Offset(0, 6)),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=1),
                            bgcolor=CHIP_BG,
                            border_radius=10,
                            content=ft.Text(category, size=10, color=TEXT_COLOR),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text("★★★★★", size=12, color=MAIN_COLOR),
                ft.Text(review, size=12, color=SUBTEXT_COLOR),
            ],
            spacing=4,
        ),
    )

def browse_result_card(item, width):
    return ft.Container(
        width=width,
        padding=SPACE_LG,
        bgcolor=ft.Colors.with_opacity(0.78, "#FFFFFF"),
        border_radius=RADIUS_XL,
        border=ft.border.all(1, ft.Colors.with_opacity(0.46, "#FFFFFF")),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=18, color="#17000000", offset=ft.Offset(0, 6)),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(item.get("title", ""), size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                                ft.Text(item.get("subtitle", ""), size=12, color=SUBTEXT_COLOR),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=8, vertical=1),
                            bgcolor=CHIP_BG,
                            border_radius=0,
                            content=ft.Text(item.get("badge", "목록"), size=10, color=TEXT_COLOR),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(item.get("meta", ""), size=12, color=TEXT_COLOR),
                ft.Text(item.get("description", ""), size=13, color=SUBTEXT_COLOR),
            ],
            spacing=8,
        ),
    )
