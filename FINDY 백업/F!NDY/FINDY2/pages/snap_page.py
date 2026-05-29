import flet as ft

def render(page, app_state, rerender):
    cards = app_state.get("snap_cards", [])

    card_list = cards if cards else [
        ft.Text("스냅 데이터가 없습니다")
    ]

    page.controls.clear()

    page.add(
        ft.Column(
            controls=[
                ft.Text("스냅", size=20),
                ft.Divider(),
                *card_list
            ],
            expand=True,
        )
    )

    page.update()
