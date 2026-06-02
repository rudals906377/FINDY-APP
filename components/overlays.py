import flet as ft
from components.layout import (
    BORDER_COLOR,
    CHIP_BG,
    FLOATING_SHADOW,
    MAIN_COLOR,
    MAIN_COLOR_SOFT,
    NAV_BAR_HEIGHT,
    NAV_SAFE_GAP,
    PHONE_HEIGHT,
    PHONE_WIDTH,
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



def overlay_bottom_spacer():
    return ft.Container(height=NAV_BAR_HEIGHT + NAV_SAFE_GAP)



def _overlay_header(title, app_icon, on_close):
    return ft.Container(
        padding=ft.padding.only(bottom=14),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            title,
                            size=24,
                            weight=ft.FontWeight.W_600,
                            color=TEXT_COLOR,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            "원하는 항목을 빠르게 탐색해보세요.",
                            size=11,
                            color=SUBTEXT_COLOR,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
                ft.Container(
                    width=40,
                    height=40,
                    border_radius=999,
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, BORDER_COLOR),
                    alignment=ft.Alignment(0, 0),
                    on_click=on_close,
                    ink=True,
                    content=ft.Icon(app_icon("CLOSE", "CLEAR"), size=18, color=TEXT_COLOR),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )



def build_left_overlay(
    *,
    app_state,
    app_icon,
    close_overlays,
    render_current_page,
    open_overlay,
    open_category_recommendations,
    left_overlay_categories,
    left_overlay_icons,
):
    def toggle_main_category(main_category):
        if app_state.get("left_menu_expanded") == main_category:
            app_state["left_menu_expanded"] = None
        else:
            app_state["left_menu_expanded"] = main_category
        open_overlay("left")
        render_current_page()

    def on_subcategory_click(main_category, sub_category):
        open_category_recommendations(main_category, sub_category)

    item_controls = []
    category_descriptions = {
        "헤어": "컷, 펌, 컬러와 스타일링",
        "네일아트": "젤, 케어, 디자인 네일",
        "포토": "프로필, 스냅, 콘셉트 촬영",
        "웨딩": "신부, 본식, 리허설 뷰티",
        "반영구": "눈썹, 아이라인, 입술 시술",
        "메이크업": "데일리, 화보, 신부 메이크업",
    }
    for main_category, small_categories in left_overlay_categories.items():
        is_expanded = app_state.get("left_menu_expanded") == main_category
        item_controls.append(
            ft.Container(
                width=340,
                padding=ft.padding.only(left=16, right=14, top=15, bottom=15),
                border_radius=26,
                bgcolor="#FFFFFF" if not is_expanded else "#FFFFFF",
                border=ft.border.all(1, ft.Colors.with_opacity(0.78, BORDER_COLOR)),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=18, color="#0E8B6B4F", offset=ft.Offset(0, 8)),
                on_click=lambda e, category=main_category: toggle_main_category(category),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=42,
                                    height=42,
                                    border_radius=16,
                                    bgcolor="#FFFFFF",
                                    border=ft.border.all(1, "#E6D7C8"),
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(app_icon(left_overlay_icons.get(main_category, "CIRCLE")), size=20, color=MAIN_COLOR),
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            main_category,
                                            size=16,
                                            color=TEXT_COLOR,
                                            weight=ft.FontWeight.W_700,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            category_descriptions.get(main_category, "카테고리 둘러보기"),
                                            size=11,
                                            color=SUBTEXT_COLOR,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                    spacing=3,
                                    expand=True,
                                ),
                            ],
                            spacing=13,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=999,
                            bgcolor="#FFFFFF",
                            border=ft.border.all(1, "#E6D7C8"),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                app_icon(
                                    "KEYBOARD_ARROW_DOWN" if is_expanded else "CHEVRON_RIGHT",
                                    "EXPAND_MORE",
                                    "ARROW_FORWARD_IOS",
                                ),
                                size=20,
                                color=MAIN_COLOR,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        if is_expanded:
            for sub_category in small_categories:
                item_controls.append(
                    ft.Container(
                        width=312,
                        margin=ft.margin.only(left=14, top=4, bottom=2),
                        padding=ft.padding.symmetric(horizontal=14, vertical=11),
                        border_radius=16,
                        bgcolor="#FFFFFF",
                        border=ft.border.all(1, ft.Colors.with_opacity(0.72, BORDER_COLOR)),
                        on_click=lambda e, main=main_category, sub=sub_category: on_subcategory_click(main, sub),
                        ink=True,
                        content=ft.Row(
                            controls=[
                                ft.Container(width=6, height=6, border_radius=999, bgcolor=MAIN_COLOR),
                                ft.Text(
                                    sub_category,
                                    size=13,
                                    color=TEXT_COLOR,
                                    weight=ft.FontWeight.W_600,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    expand=True,
                                ),
                                ft.Icon(app_icon("CHEVRON_RIGHT", "ARROW_FORWARD_IOS"), size=16, color=SUBTEXT_COLOR),
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                )

    left_overlay_visible = app_state.get("overlay") == "left"
    scrim = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        bgcolor=ft.Colors.with_opacity(0.22, "#1F1A17"),
        opacity=1.0 if left_overlay_visible else 0.0,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
    )
    panel = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        padding=22,
        opacity=1.0 if left_overlay_visible else 0.0,
        offset=ft.Offset(0, 0),
        scale=1.0,
        animate_opacity=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#FFFFFF", "#FFFFFF"],
        ),
        content=ft.Container(
            width=PHONE_WIDTH,
            height=PHONE_HEIGHT,
            border_radius=0,
            content=ft.Column(
                controls=[
                    _overlay_header("카테고리", app_icon, lambda e: (close_overlays(), render_current_page())),
                    ft.Container(height=12),
                    ft.Column(
                        controls=[*item_controls, overlay_bottom_spacer()],
                        spacing=8,
                        scroll=ft.ScrollMode.HIDDEN,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        ),
    )

    app_state["left_overlay_scrim"] = scrim
    app_state["left_overlay_panel"] = panel

    return ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        content=ft.Stack(
            controls=[
                scrim,
                ft.GestureDetector(
                    on_tap=lambda e: (close_overlays(), render_current_page()),
                    content=ft.Container(width=PHONE_WIDTH, height=PHONE_HEIGHT),
                ),
                ft.Container(
                    width=PHONE_WIDTH,
                    height=PHONE_HEIGHT,
                    alignment=ft.Alignment(-1, 0),
                    content=panel,
                ),
            ]
        ),
    )



def build_right_overlay(
    *,
    app_icon,
    close_overlays,
    render_current_page,
    build_my_info_profile_card,
    build_my_info_menu_section,
):
    scrim = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        bgcolor=ft.Colors.with_opacity(0.22, "#1F1A17"),
        opacity=1.0,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
    )
    panel = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        padding=24,
        opacity=1.0,
        offset=ft.Offset(0, 0),
        scale=1.0,
        animate_opacity=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#FFFFFF", "#FFFFFF"],
        ),
        shadow=_shadow(FLOATING_SHADOW),
        content=ft.Column(
            controls=[
                _overlay_header("내 정보", app_icon, lambda e: (close_overlays(), render_current_page())),
                ft.Container(height=12),
                build_my_info_profile_card(),
                ft.Container(height=14),
                build_my_info_menu_section(),
                overlay_bottom_spacer(),
            ],
            spacing=0,
            scroll=ft.ScrollMode.HIDDEN,
        ),
    )

    return ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        content=ft.Stack(
            controls=[
                scrim,
                ft.GestureDetector(
                    on_tap=lambda e: (close_overlays(), render_current_page()),
                    content=ft.Container(width=PHONE_WIDTH, height=PHONE_HEIGHT),
                ),
                ft.Container(
                    width=PHONE_WIDTH,
                    height=PHONE_HEIGHT,
                    alignment=ft.Alignment(1, 0),
                    content=panel,
                ),
            ]
        ),
    )
