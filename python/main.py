import os
import sys

if __package__ in (None, ""):
    # NOTE: 兼容直接执行 new_py/main.py 的场景，将上一级目录加入 sys.path，以便绝对导入包
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from new_py.ui.main import gui      # 如果你的IDE在这里报错，别管他，能跑
else:
    from .ui.main import gui

if __name__ == "__main__":
    # NOTE: 保持入口简洁，职责仅为启动 UI；业务与系统交互均在分层中完成
    gui()


"""
How To Build
uvx pyinstaller --noconfirm --clean --onefile --windowed --uac-admin --icon "path_to_ico" --upx-dir "path_to_upx" -n Disable-automatic-Windows-update ".\main.py"
"""