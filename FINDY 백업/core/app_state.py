app_state = {
    "current_page": "home",
    "selected_tab": 2,
    "selected_category": None,
    "detail_artist_id": None,
    "search_text": "",
    "search_results": [],
    "saved_ids": set(),

    "reservation_form": {
        "artist_id": None,
        "artist_name": "",
        "job": "",
        "category": "",
        "service": "",
        "date": None,
        "time": None,
        "note": "",
    },
    "reservation_history": [],
    "last_completed_reservation": None,

    "inquiries": [],
    "inquiry_draft": {
        "category": "서비스 문의",
        "title": "",
        "content": "",
    },
}
