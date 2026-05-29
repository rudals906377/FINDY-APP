import os
import flet as ft
from FINDY324 import main

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ft.app(target=main, assets_dir=os.path.join(base_dir, "assets"))
