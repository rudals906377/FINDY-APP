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
    "main.py",
    "python_files/FINDY.py",
    "python_files/FINDY2.py",
    "python_files/FINDY_customer.py",
    "python_files/FINDY_artist.py",
    "python_files/generate_placeholders.py",
    "python_files/test_findy2_services.py",
    "scripts/generate_release_assets.py",
    "auth_gateway/app.py",
    "auth_gateway/check_config.py",
    "components/layout.py",
    "components/cards.py",
    "components/overlays.py",
    "data/artists.py",
    "data/beauty_mood_keywords.py",
    "data/categories.py",
    "data/findy2_content.py",
    "data/legal_content.py",
    "data/reviews.py",
    "data/review_safety.py",
    "data/snaps.py",
    "core/app_state.py",
    "core/findy2_config.py",
    "core/findy2_state.py",
    "core/router.py",
    "services/artist_service.py",
    "services/findy2_auth.py",
    "services/findy2_media_storage.py",
    "services/findy2_social_auth.py",
    "services/findy2_user_storage.py",
    "services/reservation_storage.py",
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
    "assets/icon.png",
    "assets/splash.png",
    "assets/naver.png",
    "assets/kakao.png",
    "assets/google.png",
    "assets/apple.png",
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
    "pyproject.toml",
    "core/findy2_public_config.json",
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
    "docs/project/FINDY2_DEPLOYMENT.md",
    "docs/project/BUILD_VERIFICATION_2026-06-25.md",
    "docs/project/SOCIAL_AUTH_SETUP.md",
    "auth_gateway/app.py",
    "auth_gateway/requirements.txt",
    "auth_gateway/.env.example",
    "auth_gateway/README.md",
    "auth_gateway/Dockerfile",
    "auth_gateway/compose.yaml",
    "auth_gateway/run_local.sh",
    "docs/legal/PRIVACY_POLICY_KO.md",
    "docs/legal/TERMS_OF_SERVICE_KO.md",
    "docs/legal/COMMUNITY_GUIDELINES_KO.md",
    "docs/legal/STORE_DATA_DISCLOSURE.md",
    "docs/project/PHONE_IDENTITY_RECOVERY.md",
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
    ("python_files/FINDY2.py", "create_findy2_state()"),
    ("python_files/FINDY2.py", "def show_settings_page"),
    ("python_files/FINDY2.py", "def show_liked_content_page"),
    ("python_files/FINDY2.py", 'content_tabs = ["전체", "질문", "자유게시판", "스냅", "비디오"]'),
    ("data/beauty_mood_keywords.py", "BEAUTY_MOOD_KEYWORDS"),
    ("data/beauty_mood_keywords.py", '"반영구시술"'),
    ("data/findy2_content.py", "def default_community_posts"),
    ("data/findy2_content.py", "def default_video_items"),
    ("core/findy2_config.py", "FINDY2_RESERVATION_ENABLED = False"),
    ("core/findy2_config.py", "FINDY2_USER_DATA_PATH"),
    ("core/findy2_config.py", "FINDY2_AUTH_DATA_PATH"),
    ("core/findy2_config.py", "FINDY2_SESSION_PATH"),
    ("core/findy2_state.py", "def create_findy2_state"),
    ("services/findy2_auth.py", "def register_user"),
    ("services/findy2_auth.py", "def authenticate_user"),
    ("services/findy2_auth.py", "def restore_session"),
    ("services/findy2_auth.py", "def delete_user"),
    ("services/findy2_auth.py", "def social_login_or_register"),
    ("services/findy2_auth.py", "def read_remote_session_token"),
    ("services/findy2_media_storage.py", "def store_image"),
    ("services/findy2_media_storage.py", "def store_video"),
    ("services/findy2_media_storage.py", "def delete_user_media"),
    ("services/findy2_social_auth.py", "def start_social_auth"),
    ("services/findy2_social_auth.py", "def wait_for_social_auth"),
    ("services/findy2_social_auth.py", "def delete_social_account"),
    ("services/findy2_phone_auth.py", "def request_phone_otp"),
    ("services/findy2_phone_auth.py", "def verify_phone_otp"),
    ("services/findy2_auth.py", "def find_usernames_by_phone"),
    ("services/findy2_auth.py", "def find_user_by_phone"),
    ("services/findy2_auth.py", "def get_or_create_demo_user"),
    ("services/findy2_auth.py", "def reset_password_by_phone"),
    ("services/findy2_user_storage.py", "def save_findy2_user_data"),
    ("services/findy2_user_storage.py", "def load_findy2_user_data"),
    ("services/findy2_user_storage.py", "def user_scoped_data_path"),
    ("services/findy2_user_storage.py", "def delete_findy2_user_data"),
    ("python_files/FINDY2.py", "def show_legal_page"),
    ("python_files/FINDY2.py", "def open_account_deletion_dialog"),
    ("python_files/FINDY2.py", "def social_auth_buttons"),
    ("python_files/FINDY2.py", "async def perform_social_auth"),
    ("python_files/FINDY2.py", "def show_connected_accounts_page"),
    ("pyproject.toml", 'bundle_id = "com.findybeauty.findy2"'),
    ("core/findy2_config.py", "FINDY2_AUTH_API_URL"),
    ("auth_gateway/app.py", "def start_oauth"),
    ("auth_gateway/app.py", "def oauth_status"),
    ("auth_gateway/app.py", "def delete_account"),
    ("auth_gateway/app.py", "def request_phone_otp"),
    ("auth_gateway/app.py", "def verify_phone_otp"),
    ("python_files/FINDY2.py", "def show_account_recovery_page"),
    ("auth_gateway/app.py", "preferred_account_id"),
    ("python_files/FINDY2.py", "page.on_error = handle_page_error"),
    ("python_files/FINDY2.py", "page.on_resized = handle_page_resized"),
    ("python_files/FINDY2.py", "current_page not in public_pages"),
    ("python_files/FINDY2.py", 'regular_font_rel = "Pretendard-Regular.ttf"'),
    ("python_files/FINDY2.py", 'regular_font_rel = "Pretendard/Pretendard-Regular.ttf"'),
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

for rel in ("python_files/FINDY.py", "python_files/FINDY2.py"):
    app_path = os.path.join(BASE_DIR, rel)
    if not os.path.exists(app_path):
        continue
    with open(app_path, "r", encoding="utf-8") as f:
        app_source = f.read()
    assigned_pages = set(re.findall(r'app_state\["current_page"\]\s*=\s*"([^"]+)"', app_source))
    rendered_pages = set(re.findall(r'page_name\s*==\s*"([^"]+)"', app_source))
    missing_render_routes = sorted(assigned_pages - rendered_pages)
    if missing_render_routes:
        text_check_errors.append(f"{rel}: current_page values missing render routes: {', '.join(missing_render_routes)}")

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
