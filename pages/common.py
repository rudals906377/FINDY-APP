import flet as ft

from components.layout import (
    BG_COLOR,
    PHONE_HEIGHT,
    PHONE_WIDTH,
    NAV_BAR_HEIGHT,
    NAV_SAFE_GAP,
    MAIN_COLOR,
    MAIN_COLOR_SOFT,
    SUBTEXT_COLOR,
    TEXT_COLOR,
    BORDER_COLOR,
    SHADOW_FLOATING,
    PILL_RADIUS,
)
from core.app_state import app_state
from core import router


def app_icon(name: str):
    if hasattr(ft.Icons, name):
        return getattr(ft.Icons, name)
    return ft.Icons.CIRCLE


def _floating_shadow():
    return ft.BoxShadow(
        spread_radius=SHADOW_FLOATING["spread_radius"],
        blur_radius=SHADOW_FLOATING["blur_radius"],
        color=SHADOW_FLOATING["color"],
        offset=ft.Offset(SHADOW_FLOATING["offset_x"], SHADOW_FLOATING["offset_y"]),
    )


def _nav_pill(active: bool):
    return "#F4ECE3" if active else ft.Colors.TRANSPARENT


def nav_bar(page, render):
    def nav_item(icon_name, label, selected_idx, on_click):
        active = app_state.get("selected_tab") == selected_idx

        return ft.Container(
            expand=True,
            height=46,
            border_radius=18,
            bgcolor=_nav_pill(active),
            ink=True,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e: (on_click(), render(page)),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                controls=[
                    ft.Icon(
                        app_icon(icon_name),
                        size=18,
                        color=MAIN_COLOR if active else SUBTEXT_COLOR,
                    ),
                    ft.Text(
                        label,
                        size=10,
                        color=MAIN_COLOR if active else SUBTEXT_COLOR,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    return ft.Container(
        height=70,
        margin=ft.margin.only(left=14, right=14, bottom=10),
        padding=ft.padding.only(left=10, right=10, top=8, bottom=8),
        bgcolor="#FFFFFF",
        border_radius=28,
        border=ft.border.all(1, ft.Colors.with_opacity(0.7, BORDER_COLOR)),
        shadow=_floating_shadow(),
        content=ft.Row(
            controls=[
                nav_item("MENU", "카테고리", 0, router.go_category),
                nav_item("PHOTO_LIBRARY_OUTLINED", "스냅", 1, router.go_snap),
                nav_item("HOME_OUTLINED", "홈", 2, router.go_home),
                nav_item("SMART_DISPLAY_OUTLINED", "비디오", 3, router.go_video),
                nav_item("PERSON_OUTLINE", "내정보", 4, router.go_my),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def top_glow():
    return ft.Container(
        width=PHONE_WIDTH,
        height=140,
        top=-30,
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.12, MAIN_COLOR_SOFT),
        blur=60,
    )


def shell(page, rerender, body, include_nav=True):
    nav_height = NAV_BAR_HEIGHT + NAV_SAFE_GAP if include_nav else 18

    scroll_body = ft.Column(
        controls=[
            ft.Container(height=10),
            body,
            ft.Container(height=nav_height),
        ],
        spacing=0,
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
    )

    phone_frame = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        bgcolor="#FFFFFF",
        border_radius=36,
        shadow=_floating_shadow(),
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        content=ft.Stack(
            controls=[
                top_glow(),
                ft.Container(
                    expand=True,
                    padding=ft.padding.only(top=18, bottom=8),
                    content=scroll_body,
                ),
            ]
        ),
    )

    controls = [phone_frame]

    if include_nav:
        controls.append(
            ft.Container(
                width=PHONE_WIDTH,
                height=92,
                bottom=0,
                left=0,
                right=0,
                alignment=ft.Alignment(0, 1),
                content=nav_bar(page, rerender),
            )
        )

    page.clean()
    page.bgcolor = BG_COLOR
    page.add(
        ft.Container(
            expand=True,
            bgcolor=BG_COLOR,
            alignment=ft.Alignment(0, 0),
            content=ft.Stack(
                width=PHONE_WIDTH,
                height=PHONE_HEIGHT,
                controls=controls,
            ),
        )
    )
    page.update()


def floating_close_button(on_click):
    return ft.Container(
        width=44,
        height=44,
        border_radius=PILL_RADIUS,
        bgcolor="#FFFFFF",
        border=ft.border.all(1, BORDER_COLOR),
        shadow=_floating_shadow(),
        ink=True,
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(
            ft.Icons.CLOSE_ROUNDED,
            size=20,
            color=TEXT_COLOR,
        ),
    )
