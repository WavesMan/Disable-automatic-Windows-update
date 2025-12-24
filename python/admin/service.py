import sys
import ctypes


def is_admin() -> bool:
    # NOTE: 需要在执行注册表写入与系统设置变更前做权限门禁，避免界面层触发后才失败
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin() -> None:
    # NOTE: 当检测到非管理员权限时，使用系统外壳以提升权限重新启动当前进程；
    #       选择保留原始参数以保证用户意图不变，避免因参数丢失导致行为差异
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None,
        1,
    )
    sys.exit()

