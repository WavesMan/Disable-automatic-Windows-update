import sys
import ctypes
import logging
import traceback

from ..utils.logger import log_event


def is_admin() -> bool:
    # NOTE: 需要在执行注册表写入与系统设置变更前做权限门禁，避免界面层触发后才失败
    try:
        ok = bool(ctypes.windll.shell32.IsUserAnAdmin())
        log_event(logging.INFO, "admin_check", "管理员权限检查完成", action="admin_check", status=("ok" if ok else "not_admin"))
        return ok
    except Exception as e:
        log_event(
            logging.ERROR,
            "admin_check_failed",
            f"管理员权限检查失败: {e}",
            action="admin_check",
            status="failed",
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            exc_info=True,
        )
        return False


def run_as_admin() -> None:
    # NOTE: 当检测到非管理员权限时，使用系统外壳以提升权限重新启动当前进程；
    #       选择保留原始参数以保证用户意图不变，避免因参数丢失导致行为差异
    try:
        log_event(logging.INFO, "elevation_requested", "请求管理员权限重新启动", action="run_as_admin", status="started")
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            " ".join(sys.argv),
            None,
            1,
        )
        log_event(logging.INFO, "elevation_requested", "已发起提权重启请求", action="run_as_admin", status="ok")
    except Exception as e:
        log_event(
            logging.ERROR,
            "elevation_request_failed",
            f"提权请求失败: {e}",
            action="run_as_admin",
            status="failed",
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            exc_info=True,
        )
    sys.exit()

