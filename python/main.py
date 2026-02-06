import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from python.ui.main import gui
else:
    from .ui.main import gui

if __name__ == "__main__":
    # NOTE: 保持入口简洁，职责仅为启动 UI；业务与系统交互均在分层中完成
    gui()


r"""
How To Build
uvx pyinstaller --noconfirm --clean --onefile --windowed --uac-admin --icon "path_to_ico" --upx-dir "path_to_upx" -n Disable-automatic-Windows-update ".\main.py"
"""
