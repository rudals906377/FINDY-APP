import flet as ft
from components.layout import MAIN_COLOR, SUBTEXT_COLOR, TEXT_COLOR, PHONE_WIDTH, PHONE_HEIGHT, NAV_BAR_HEIGHT, NAV_SAFE_GAP, BORDER_COLOR

def overlay_bottom_spacer():
    return ft.Container(height=NAV_BAR_HEIGHT + NAV_SAFE_GAP)

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
    for main_category, small_categories in left_overlay_categories.items():
        is_expanded = app_state.get("left_menu_expanded") == main_category
        item_controls.append(
            ft.Container(
                width=340,
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                border_radius=18,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, BORDER_COLOR),
                on_click=lambda e, category=main_category: toggle_main_category(category),
                ink=True,
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(app_icon(left_overlay_icons.get(main_category, "CIRCLE")), size=17, color=MAIN_COLOR),
                                ft.Text(main_category, size=15, color=TEXT_COLOR, weight=ft.FontWeight.W_600),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Icon(
                            app_icon(
                                "KEYBOARD_ARROW_DOWN" if is_expanded else "CHEVRON_RIGHT",
                                "EXPAND_MORE",
                                "ARROW_FORWARD_IOS",
                            ),
                            size=20,
                            color=SUBTEXT_COLOR,
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
                        width=320,
                        margin=ft.margin.only(left=18, top=4),
                        padding=ft.padding.symmetric(horizontal=14, vertical=9),
                        border_radius=16,
                        bgcolor="#FFFFFF",
                        border=ft.border.all(1, BORDER_COLOR),
                        on_click=lambda e, main=main_category, sub=sub_category: on_subcategory_click(main, sub),
                        ink=True,
                        content=ft.Row(
                            controls=[
                                ft.Container(width=6, height=6, border_radius=999, bgcolor=MAIN_COLOR),
                                ft.Text(sub_category, size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_500),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                )

    left_overlay_visible = app_state.get("overlay") == "left"
    scrim = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        bgcolor=ft.Colors.with_opacity(0.18, "#000000"),
        opacity=1.0 if left_overlay_visible else 0.0,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
    )
    panel = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        bgcolor="#FFFFFF",
        padding=20,
        opacity=1.0 if left_overlay_visible else 0.0,
        offset=ft.Offset(0, 0),
        scale=1.0,
        animate_opacity=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("카테고리", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.IconButton(
                            icon=app_icon("CLOSE", "CLEAR"),
                            icon_color=TEXT_COLOR,
                            on_click=lambda e: (close_overlays(), render_current_page()),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=8),
                ft.Column(
                    controls=[*item_controls, overlay_bottom_spacer()],
                    spacing=4,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
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
        bgcolor=ft.Colors.with_opacity(0.18, "#000000"),
        opacity=1.0,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
    )
    panel = ft.Container(
        width=PHONE_WIDTH,
        height=PHONE_HEIGHT,
        bgcolor="#FFFFFF",
        padding=24,
        opacity=1.0,
        offset=ft.Offset(0, 0),
        scale=1.0,
        animate_opacity=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        animate_offset=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("내정보", size=26, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.IconButton(
                            icon=app_icon("CLOSE", "CLEAR"),
                            icon_color=TEXT_COLOR,
                            on_click=lambda e: (close_overlays(), render_current_page()),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=12),
                build_my_info_profile_card(),
                ft.Container(height=14),
                build_my_info_menu_section(),
                overlay_bottom_spacer(),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
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
