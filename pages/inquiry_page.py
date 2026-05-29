from datetime import datetime
import flet as ft

from components.cards import page_header, hero_card, browse_result_card, soft_button, chip, section_title
from components.layout import CONTENT_WIDTH, SPACE_MD, SPACE_LG, MAIN_COLOR, SUBTEXT_COLOR, BORDER_COLOR
from core import router
from .common import shell


INQUIRY_CATEGORIES = ["서비스 문의", "예약 문의", "계정 문의", "기타"]



def _ensure_state(app_state):
    app_state.setdefault("inquiries", [])
    app_state.setdefault(
        "inquiry_draft",
        {
            "category": INQUIRY_CATEGORIES[0],
            "title": "",
            "content": "",
        },
    )



def _status_badge(status: str):
    color = MAIN_COLOR if status == "접수 완료" else "#4F8A5B"
    bg = "#F8F2EC" if status == "접수 완료" else "#EDF7EF"
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=999,
        bgcolor=bg,
        content=ft.Text(status, size=10, color=color, weight=ft.FontWeight.W_500),
    )



def _inquiry_card(item):
    return ft.Container(
        width=CONTENT_WIDTH,
        padding=ft.padding.all(16),
        bgcolor="#FFFFFF",
        border_radius=24,
        border=ft.border.all(1, "#E6D7C8"),
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(item.get("title", "제목 없음"), size=15, weight=ft.FontWeight.W_500, color="#3B2F27"),
                                ft.Text(item.get("category", ""), size=11, color=SUBTEXT_COLOR),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        _status_badge(item.get("status", "접수 완료")),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Text(item.get("content", ""), size=12, color="#5F584F"),
                ft.Text(item.get("created_at", ""), size=10, color="#C8BAAE"),
            ],
            spacing=10,
        ),
    )



def render(page, app_state, rerender):
    _ensure_state(app_state)
    draft = app_state["inquiry_draft"]
    inquiries = list(reversed(app_state.get("inquiries", [])))

    title_field = ft.TextField(
        width=CONTENT_WIDTH,
        value=draft.get("title", ""),
        hint_text="문의 제목을 입력해주세요.",
        border_radius=16,
        bgcolor="#FFFFFF",
        border_color=BORDER_COLOR,
        focused_border_color=MAIN_COLOR,
        cursor_color=MAIN_COLOR,
        content_padding=16,
        on_change=lambda e: draft.__setitem__("title", e.control.value or ""),
    )

    content_field = ft.TextField(
        width=CONTENT_WIDTH,
        value=draft.get("content", ""),
        hint_text="불편한 점이나 궁금한 내용을 자세히 적어주세요.",
        multiline=True,
        min_lines=5,
        max_lines=8,
        border_radius=16,
        bgcolor="#FFFFFF",
        border_color=BORDER_COLOR,
        focused_border_color=MAIN_COLOR,
        cursor_color=MAIN_COLOR,
        content_padding=16,
        on_change=lambda e: draft.__setitem__("content", e.control.value or ""),
    )

    category_row = ft.Row(
        controls=[
            chip(
                category,
                selected=(draft.get("category") == category),
                on_click=lambda e, value=category: (draft.__setitem__("category", value), rerender(page)),
            )
            for category in INQUIRY_CATEGORIES
        ],
        wrap=True,
        spacing=8,
        run_spacing=8,
        width=CONTENT_WIDTH,
    )

    def submit_inquiry(e):
        title = (draft.get("title") or "").strip()
        content = (draft.get("content") or "").strip()
        category = draft.get("category") or INQUIRY_CATEGORIES[0]

        if not title or not content:
            page.snack_bar = ft.SnackBar(content=ft.Text("제목과 내용을 모두 입력해주세요."), bgcolor="#B85C5C")
            page.snack_bar.open = True
            page.update()
            return

        inquiries_store = app_state.setdefault("inquiries", [])
        inquiries_store.append(
            {
                "id": f"q{len(inquiries_store) + 1}",
                "category": category,
                "title": title,
                "content": content,
                "status": "접수 완료",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        app_state["inquiry_draft"] = {
            "category": INQUIRY_CATEGORIES[0],
            "title": "",
            "content": "",
        }
        page.snack_bar = ft.SnackBar(content=ft.Text("문의가 접수되었어요."), bgcolor=MAIN_COLOR)
        page.snack_bar.open = True
        rerender(page)

    body_controls = [
        page_header(
            "문의내역",
            on_back=lambda e: (router.go_my(), rerender(page)),
            width=CONTENT_WIDTH,
            subtitle="문의 작성과 접수된 내역 확인을 한 화면에서 할 수 있어요.",
        ),
        hero_card(
            "1:1 문의",
            "DB 없이도 앱 안에서 바로 접수하고 내역을 확인할 수 있어요.",
            CONTENT_WIDTH,
            emoji="💬",
        ),
        section_title("문의 카테고리", "문의 유형을 먼저 선택해주세요.", width=CONTENT_WIDTH),
        category_row,
        section_title("문의 제목", width=CONTENT_WIDTH),
        title_field,
        section_title("문의 내용", "가능한 자세히 적을수록 더 정확하게 확인할 수 있어요.", width=CONTENT_WIDTH),
        content_field,
        soft_button("문의 접수하기", MAIN_COLOR, "white", submit_inquiry, width=CONTENT_WIDTH, height=56),
        section_title("접수된 문의", "앱을 켠 동안 작성한 문의를 바로 확인할 수 있어요.", width=CONTENT_WIDTH),
    ]

    if inquiries:
        body_controls.extend([_inquiry_card(item) for item in inquiries])
    else:
        body_controls.append(
            browse_result_card(
                {
                    "title": "아직 문의한 내역이 없어요",
                    "subtitle": "첫 문의를 남겨보세요",
                    "meta": "문의내역",
                    "description": "궁금한 점이나 개선 의견이 있으면 위 양식으로 바로 문의할 수 있어요.",
                    "badge": "EMPTY",
                },
                CONTENT_WIDTH,
            )
        )

    body_controls.append(ft.Container(height=SPACE_LG))

    body = ft.Column(
        controls=body_controls,
        spacing=SPACE_MD,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    shell(page, rerender, body, include_nav=False)
