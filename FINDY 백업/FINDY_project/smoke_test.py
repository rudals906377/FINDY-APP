import os
import sys
import py_compile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

files = [
    "FINDY324.py",
    "components/layout.py",
    "components/cards.py",
    "components/overlays.py",
    "data/artists.py",
    "data/categories.py",
    "data/reviews.py",
    "data/snaps.py",
    "core/app_state.py",
    "core/router.py",
    "services/artist_service.py",
    "services/reservation_service.py",
    "pages/common.py",
    "pages/opening_page.py",
    "pages/login_page.py",
    "pages/home_page.py",
    "pages/my_page.py",
    "pages/detail_page.py",
    "pages/reservation_page.py",
    "pages/reservation_confirm_page.py",
    "pages/reservation_complete_page.py",
    "pages/reservation_history_page.py",
    "pages/support_page.py",
    "pages/inquiry_page.py",
    "pages/completed_page.py",
    "pages/beauty_profile_page.py",
    "pages/notice_page.py",
    "pages/feedback_page.py",
]

missing = []
compile_errors = []

for rel in files:
    path = os.path.join(BASE_DIR, rel)
    if not os.path.exists(path):
        missing.append(rel)
        continue
    try:
        py_compile.compile(path, doraise=True)
    except Exception as e:
        compile_errors.append(f"{rel}: {e}")

asset_files = [
    "assets/Pretendard-Regular.ttf",
    "assets/Pretendard-Bold.ttf",
    "assets/findy_opening_screen.png",
    "assets/findy_login_logo_transparent.png",
]

for rel in asset_files:
    if not os.path.exists(os.path.join(BASE_DIR, rel)):
        missing.append(rel)

if missing or compile_errors:
    if missing:
        print("FAILED - Missing:")
        for item in missing:
            print(f"  - {item}")
    if compile_errors:
        print("FAILED - Compile errors:")
        for item in compile_errors:
            print(f"  - {item}")
    sys.exit(1)

print("OK: compile and asset checks passed")
sys.exit(0)
