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
pwsh -ExecutionPolicy Bypass -File .\build.ps1 -UpxDir "C:\Users\diwei\PyCharmMiscProject\upx"
"""
