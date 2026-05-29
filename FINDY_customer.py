import os

import flet as ft

os.environ["FINDY_APP_MODE"] = "customer"

from FINDY324 import ASSETS_DIR, main


if __name__ == "__main__":
    ft.app(target=main, assets_dir=ASSETS_DIR if os.path.isdir(ASSETS_DIR) else None)
