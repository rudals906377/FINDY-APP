import os

import flet as ft

from python_files.FINDY2 import main


if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    ft.app(target=main, assets_dir=assets_dir)
