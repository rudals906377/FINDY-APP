import os, sys, py_compile
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
files = ["FINDY324.py","main.py","components/layout.py","components/cards.py","components/overlays.py","data/artists.py","data/categories.py","data/reviews.py","data/snaps.py"]
missing=[]
for rel in files:
    path=os.path.join(BASE_DIR, rel)
    if not os.path.exists(path): missing.append(rel)
    else: py_compile.compile(path, doraise=True)
for rel in ["assets/Pretendard-Regular.ttf","assets/Pretendard-Bold.ttf","assets/findy_opening_screen.png","assets/findy_login_logo_transparent.png"]:
    if not os.path.exists(os.path.join(BASE_DIR, rel)): missing.append(rel)
print("OK: compile and asset checks passed" if not missing else "FAILED: " + ", ".join(missing))
sys.exit(0 if not missing else 1)
