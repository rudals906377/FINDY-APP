from .app_state import app_state

def go(page_name: str):
    app_state["current_page"] = page_name

def go_tab(page_name: str, idx: int):
    app_state["current_page"] = page_name
    app_state["selected_tab"] = idx

def go_home():
    go_tab("home", 2)

def go_category():
    go_tab("category", 0)

def go_snap():
    go_tab("snap", 1)

def go_video():
    go_tab("video", 3)

def go_my():
    go_tab("my", 4)

def go_detail(artist_id: str):
    app_state["detail_artist_id"] = artist_id
    app_state["current_page"] = "detail"

def go_reservation():
    app_state["current_page"] = "reservation"

def go_reservation_confirm():
    app_state["current_page"] = "reservation_confirm"

def go_reservation_complete():
    app_state["current_page"] = "reservation_complete"

def go_reservation_history():
    app_state["current_page"] = "reservation_history"
    app_state["selected_tab"] = 4
