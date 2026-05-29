import flet as ft

def render(page, app_state, rerender):
    featured_controls = app_state.get("featured_controls", [])

    # 안전한 처리
    featured_list = featured_controls if featured_controls else [
        ft.Text("추천 아티스트가 없습니다")
    ]

    page.controls.clear()

    page.add(
        ft.Column(
            controls=[
                ft.Text("홈", size=20),
                ft.Divider(),
                *featured_list
            ],
            expand=True,
        )
    )

    page.update()
