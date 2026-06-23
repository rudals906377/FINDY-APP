import os
import re
import sys
import py_compile
from html.parser import HTMLParser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# macOS can route py_compile output to ~/Library/Caches, which may be blocked
# in sandboxed/dev-tool environments. Keep bytecode inside the project unless
# the caller explicitly chose another cache prefix.
if not os.environ.get("PYTHONPYCACHEPREFIX"):
    cache_prefix = os.path.join(BASE_DIR, ".pycache_smoke")
    os.environ["PYTHONPYCACHEPREFIX"] = cache_prefix
    sys.pycache_prefix = cache_prefix

files = [
    "python_files/FINDY.py",
    "python_files/FINDY2.py",
    "python_files/FINDY_customer.py",
    "python_files/FINDY_artist.py",
    "python_files/generate_placeholders.py",
    "components/layout.py",
    "components/cards.py",
    "components/overlays.py",
    "data/artists.py",
    "data/beauty_mood_keywords.py",
    "data/categories.py",
    "data/reviews.py",
    "data/review_safety.py",
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
    "assets/app_logo/app_findy_logo_horizontal.png",
    "assets/app_logo/app_findy_logo_wordmark.png",
    "assets/app_logo/app_findy_logo_vertical.png",
    "assets/app_logo/app_findy_logo_mark.png",
    "assets/app_logo/app_findy_logo_mark_shell.png",
    "assets/app_logo/app_findy_opening_logo.png",
    "python_files/generate_placeholders.py",
]

release_files = [
    "README.md",
    "requirements.txt",
    "docs/README.md",
    "docs/apps/FINDY.md",
    "docs/apps/FINDY2.md",
    "docs/apps/FINDY_customer.md",
    "docs/apps/FINDY_artist.md",
    "docs/project/README.md",
    "docs/project/RELEASE_CHECKLIST.md",
    "docs/project/QA_CHECKLIST.md",
    "docs/project/BEAUTY_KEYWORD_TAXONOMY.md",
    "docs/project/NEXT_STEPS.md",
    "docs/artist/README.md",
]

text_checks = [
    ("python_files/FINDY_customer.py", 'os.environ["FINDY_APP_MODE"] = "customer"'),
    ("python_files/FINDY_artist.py", 'os.environ["FINDY_APP_MODE"] = "artist"'),
    ("python_files/FINDY.py", "def show_login_page"),
    ("python_files/FINDY.py", "def show_home_page"),
    ("python_files/FINDY.py", "def show_category_page"),
    ("python_files/FINDY.py", "def show_snap_page"),
    ("python_files/FINDY.py", "def show_video_page"),
    ("python_files/FINDY.py", "def show_my_page"),
    ("python_files/FINDY.py", "def show_artist_main_page"),
    ("python_files/FINDY.py", "def show_artist_portfolio_page"),
    ("python_files/FINDY.py", "def show_artist_portfolio_add_page"),
    ("python_files/FINDY.py", "def show_artist_profile_page"),
    ("python_files/FINDY.py", "def show_artist_reservation_manage_page"),
    ("python_files/FINDY.py", "def show_artist_review_manage_page"),
    ("python_files/FINDY.py", "def show_artist_price_menu_page"),
    ("python_files/FINDY2.py", "def show_community_board_page"),
    ("python_files/FINDY2.py", "def default_community_posts"),
    ("python_files/FINDY2.py", "def show_settings_page"),
    ("python_files/FINDY2.py", "def show_liked_content_page"),
    ("python_files/FINDY2.py", 'content_tabs = ["전체", "질문", "자유게시판", "스냅", "비디오"]'),
    ("data/beauty_mood_keywords.py", "BEAUTY_MOOD_KEYWORDS"),
    ("data/beauty_mood_keywords.py", '"반영구시술"'),
    ("docs/project/BEAUTY_KEYWORD_TAXONOMY.md", "FINDY2 뷰티 감성어/추천 키워드 사전"),
    ("components/layout.py", 'MAIN_COLOR = "#8B6B4F"'),
    ("components/layout.py", 'BORDER_COLOR = "#E6D7C8"'),
    ("components/layout.py", 'CARD_COLOR = "#FFFFFF"'),
]

font_groups = [
    ("assets/Pretendard-Regular.ttf", "assets/Pretendard-Bold.ttf"),
    ("assets/Pretendard/Pretendard-Regular.ttf", "assets/Pretendard/Pretendard-Bold.ttf"),
]
if not any(all(os.path.exists(os.path.join(BASE_DIR, rel)) for rel in group) for group in font_groups):
    missing.append("assets/Pretendard-Regular.ttf or assets/Pretendard/Pretendard-Regular.ttf")
    missing.append("assets/Pretendard-Bold.ttf or assets/Pretendard/Pretendard-Bold.ttf")

for rel in asset_files:
    if not os.path.exists(os.path.join(BASE_DIR, rel)):
        missing.append(rel)

for rel in release_files:
    if not os.path.exists(os.path.join(BASE_DIR, rel)):
        missing.append(rel)

text_check_errors = []
for rel, expected in text_checks:
    path = os.path.join(BASE_DIR, rel)
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if expected not in content:
        text_check_errors.append(f"{rel}: missing `{expected}`")

findy_path = os.path.join(BASE_DIR, "python_files", "FINDY.py")
if os.path.exists(findy_path):
    with open(findy_path, "r", encoding="utf-8") as f:
        findy_source = f.read()
    assigned_pages = set(re.findall(r'app_state\["current_page"\]\s*=\s*"([^"]+)"', findy_source))
    rendered_pages = set(re.findall(r'page_name\s*==\s*"([^"]+)"', findy_source))
    missing_render_routes = sorted(assigned_pages - rendered_pages)
    if missing_render_routes:
        text_check_errors.append(f"python_files/FINDY.py: current_page values missing render routes: {', '.join(missing_render_routes)}")

web_index = os.path.join(BASE_DIR, "web", "index.html")
if os.path.exists(web_index):
    try:
        parser = HTMLParser()
        with open(web_index, "r", encoding="utf-8") as f:
            parser.feed(f.read())
    except Exception as e:
        compile_errors.append(f"web/index.html: {e}")
else:
    missing.append("web/index.html")

if missing or compile_errors or text_check_errors:
    if missing:
        print("FAILED - Missing:")
        for item in missing:
            print(f"  - {item}")
    if compile_errors:
        print("FAILED - Compile errors:")
        for item in compile_errors:
            print(f"  - {item}")
    if text_check_errors:
        print("FAILED - Text checks:")
        for item in text_check_errors:
            print(f"  - {item}")
    sys.exit(1)

print("OK: compile, asset, route, brand, and web checks passed")
sys.exit(0)
