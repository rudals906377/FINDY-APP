import flet as ft
from .layout import (
    CARD_COLOR,
    CHIP_BG,
    MAIN_COLOR,
    MAIN_COLOR_DARK,
    MAIN_COLOR_SOFT,
    SPACE_SM,
    SPACE_MD,
    SPACE_LG,
    RADIUS_MD,
    RADIUS_LG,
    RADIUS_XL,
    PILL_RADIUS,
    SUBTEXT_COLOR,
    TEXT_COLOR,
    TEXT_STRONG,
    BORDER_COLOR,
    DIVIDER_COLOR,
    SHADOW_SOFT,
    SHADOW_CARD,
)

def _shadow(config):
    return ft.BoxShadow(
        spread_radius=config["spread_radius"],
        blur_radius=config["blur_radius"],
        color=config["color"],
        offset=ft.Offset(config["offset_x"], config["offset_y"]),
    )

def page_header(title, on_back=None, width=None, subtitle=None, trailing=None):
    leading = (
        ft.Container(
            width=38,
            height=38,
            border_radius=PILL_RADIUS,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, BORDER_COLOR),
            alignment=ft.Alignment(0, 0),
            on_click=on_back,
            ink=True,
            shadow=_shadow(SHADOW_SOFT),
            content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, size=16, color=TEXT_STRONG),
        )
        if on_back else
        ft.Container(width=38, height=38)
    )

    header_row = ft.Row(
        controls=[
            leading,
            ft.Column(
                controls=[
                    ft.Text(title, size=24, weight=ft.FontWeight.W_600, color=TEXT_STRONG),
                    ft.Text(subtitle, size=12, color=SUBTEXT_COLOR) if subtitle else ft.Container(height=0),
                ],
                spacing=4,
                expand=True,
            ),
            trailing or ft.Container(width=8),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(width=width, padding=ft.padding.only(bottom=4), content=header_row)

def section_title(title, subtitle=None, on_click=None, width=None):
    trailing = ft.Row(
        controls=[
            ft.Text("전체보기", size=11, color=MAIN_COLOR_DARK),
            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=12, color=MAIN_COLOR_DARK),
        ],
        spacing=3,
        visible=on_click is not None,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        width=width,
        padding=ft.padding.symmetric(horizontal=2),
        on_click=on_click,
        ink=on_click is not None,
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(title, size=18, weight=ft.FontWeight.W_500, color=TEXT_STRONG),
                        ft.Text(subtitle, size=11, color=SUBTEXT_COLOR) if subtitle else ft.Container(height=0),
                    ],
                    spacing=4,
                    expand=True,
                ),
                trailing,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.END,
        ),
    )

def _button_base(label, *, bgcolor, text_color, border, on_click, width, height, icon, shadow):
    return ft.Container(
        width=width,
        height=height,
        bgcolor=bgcolor,
        border_radius=18,
        border=border,
        on_click=on_click,
        ink=True,
        shadow=_shadow(shadow) if shadow else None,
        animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        content=ft.Row(
            controls=[
                ft.Icon(icon, size=16, color=text_color) if icon else ft.Container(width=0),
                ft.Text(label, color=text_color, size=15, weight=ft.FontWeight.W_500),
            ],
            spacing=8 if icon else 0,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def primary_button(label, on_click, width=300, height=52, icon=None):
    """Filled mocha CTA — 가장 중요한 단일 행동."""
    return _button_base(
        label,
        bgcolor=MAIN_COLOR,
        text_color="#FFFFFF",
        border=ft.border.all(1, MAIN_COLOR),
        on_click=on_click,
        width=width,
        height=height,
        icon=icon,
        shadow=SHADOW_SOFT,
    )


def secondary_button(label, on_click, width=300, height=52, icon=None):
    """White surface with subtle border — 보조 행동."""
    return _button_base(
        label,
        bgcolor="#FFFFFF",
        text_color=MAIN_COLOR_DARK,
        border=ft.border.all(1, BORDER_COLOR),
        on_click=on_click,
        width=width,
        height=height,
        icon=icon,
        shadow=SHADOW_SOFT,
    )


def ghost_button(label, on_click, width=300, height=44, icon=None):
    """Borderless text-only — 가장 약한 보조 링크."""
    return _button_base(
        label,
        bgcolor=ft.Colors.TRANSPARENT,
        text_color=SUBTEXT_COLOR,
        border=None,
        on_click=on_click,
        width=width,
        height=height,
        icon=icon,
        shadow=None,
    )


def soft_button(label, bgcolor, text_color, on_click, border=None, width=300, height=52, icon=None):
    """Backward-compat shim. Prefer primary_button / secondary_button / ghost_button."""
    if bgcolor == MAIN_COLOR:
        return primary_button(label, on_click, width=width, height=height, icon=icon)
    if bgcolor in (CARD_COLOR, "#FFFFFF"):
        return secondary_button(label, on_click, width=width, height=height, icon=icon)
    return _button_base(
        label,
        bgcolor=bgcolor,
        text_color=text_color,
        border=border or ft.border.all(1, BORDER_COLOR),
        on_click=on_click,
        width=width,
        height=height,
        icon=icon,
        shadow=SHADOW_SOFT,
    )

def chip(label, selected=False, on_click=None):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=14, vertical=9),
        bgcolor=MAIN_COLOR_SOFT if selected else CHIP_BG,
        border_radius=PILL_RADIUS,
        border=ft.border.all(1, MAIN_COLOR if selected else BORDER_COLOR),
        on_click=on_click,
        ink=on_click is not None,
        animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        content=ft.Text(
            label,
            size=12,
            color=MAIN_COLOR_DARK if selected else TEXT_COLOR,
            weight=ft.FontWeight.W_500 if selected else ft.FontWeight.W_500,
        ),
    )

def review_card(name, category, review, width, photos=None, rating=5):
    def review_photo_stack():
        stack_items = []
        photo_sources = list(photos or [])[:3]
        offsets = [(18, 10), (9, 5), (0, 0)]
        for idx, (left, top) in enumerate(offsets):
            source = photo_sources[idx] if idx < len(photo_sources) else None
            stack_items.append(
                ft.Container(
                    left=left,
                    top=top,
                    width=48,
                    height=48,
                    border_radius=13,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    bgcolor="#000000",
                    border=ft.border.all(2, "#FFFFFF"),
                    content=ft.Image(src=source, width=48, height=48, fit=ft.ImageFit.COVER) if source else None,
                )
            )
        return ft.Container(
            width=66,
            height=60,
            content=ft.Stack(controls=stack_items),
        )

    body_controls = [
        ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(name, size=15, weight=ft.FontWeight.W_500, color=TEXT_STRONG),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=CHIP_BG,
                                    border_radius=10,
                                    border=ft.border.all(1, BORDER_COLOR),
                                    content=ft.Text(category, size=10, color=TEXT_COLOR),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.STAR_ROUNDED, size=14, color=MAIN_COLOR if i < rating else BORDER_COLOR)
                                for i in range(5)
                            ],
                            spacing=1,
                        ),
                    ],
                    spacing=3,
                    expand=True,
                ),
                ft.Container(
                    width=66,
                    height=60,
                    content=review_photo_stack(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        ft.Text(review, size=12, color=SUBTEXT_COLOR),
    ]
    if photos:
        body_controls.append(
            ft.Container(
                margin=ft.margin.only(top=4),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            width=68,
                            height=68,
                            border_radius=8,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            content=ft.Image(src=p, width=68, height=68, fit=ft.ImageFit.COVER),
                        )
                        for p in photos[:10]
                    ],
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )
    return ft.Container(
        width=width,
        padding=SPACE_LG,
        bgcolor="#FFFFFF",
        border_radius=RADIUS_LG,
        border=ft.border.all(1, BORDER_COLOR),
        shadow=_shadow(SHADOW_CARD),
        content=ft.Column(controls=body_controls, spacing=8),
    )

def browse_result_card(item, width, on_click=None):
    return ft.Container(
        width=width,
        padding=SPACE_LG,
        bgcolor="#FFFFFF",
        border_radius=RADIUS_XL,
        border=ft.border.all(1, BORDER_COLOR),
        on_click=on_click,
        ink=on_click is not None,
        shadow=_shadow(SHADOW_CARD),
        animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(item.get("title", ""), size=16, weight=ft.FontWeight.W_500, color=TEXT_STRONG),
                                ft.Text(item.get("subtitle", ""), size=12, color=SUBTEXT_COLOR),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            bgcolor=MAIN_COLOR_SOFT,
                            border_radius=12,
                            border=ft.border.all(1, BORDER_COLOR),
                            content=ft.Text(item.get("badge", "목록"), size=10, color=MAIN_COLOR_DARK, weight=ft.FontWeight.W_500),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=1, bgcolor=DIVIDER_COLOR),
                ft.Text(item.get("meta", ""), size=12, color=TEXT_COLOR),
                ft.Text(item.get("description", ""), size=13, color=SUBTEXT_COLOR),
            ],
            spacing=10,
        ),
    )

def text_field(
    hint,
    width=300,
    password=False,
    can_reveal_password=False,
    prefix_icon=None,
    on_change=None,
    value=None,
    multiline=False,
    min_lines=1,
    max_lines=1,
):
    return ft.TextField(
        width=width,
        hint_text=hint,
        value=value,
        password=password,
        can_reveal_password=can_reveal_password,
        prefix_icon=prefix_icon,
        on_change=on_change,
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines,
        border_radius=16,
        bgcolor="#FFFFFF",
        border_color=BORDER_COLOR,
        focused_border_color=MAIN_COLOR,
        cursor_color=MAIN_COLOR,
        text_size=14,
        hint_style=ft.TextStyle(color=SUBTEXT_COLOR, size=13),
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


def auth_button(label, icon_path=None, on_click=None, width=300):
    icon = ft.Image(src=icon_path, width=18, height=18, fit="contain") if icon_path else ft.Container(width=18, height=18)
    return ft.Container(
        width=width,
        height=54,
        bgcolor="#FFFFFF",
        border_radius=18,
        border=ft.border.all(1, BORDER_COLOR),
        on_click=on_click,
        ink=True,
        shadow=_shadow(SHADOW_SOFT),
        content=ft.Row(
            controls=[icon, ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=TEXT_STRONG)],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

def hero_card(title, subtitle, width, emoji="✨"):
    return ft.Container(
        width=width,
        padding=SPACE_LG,
        bgcolor="#FFFFFF",
        border_radius=RADIUS_XL,
        border=ft.border.all(1, BORDER_COLOR),
        shadow=_shadow(SHADOW_CARD),
        content=ft.Row(
            controls=[
                ft.Container(
                    width=52,
                    height=52,
                    border_radius=22,
                    bgcolor=MAIN_COLOR_SOFT,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(emoji, size=24),
                ),
                ft.Column(
                    controls=[
                        ft.Text(title, size=17, weight=ft.FontWeight.W_500, color=TEXT_STRONG),
                        ft.Text(subtitle, size=12, color=SUBTEXT_COLOR),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
