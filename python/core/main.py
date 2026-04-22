from ..utils.registry_adapter import RegistryAdapter
from .services import (
    UpdateService,
    DefenderService,
    OneDriveService,
    VersionService,
    LogExporter,
    FirewallService,
)
import logging
import time
import traceback
from ..utils.logger import log_event


def _default_times() -> tuple[str, str]:
    # NOTE: 默认暂停窗口为长期占位，避免系统自动恢复；具体策略可后续外置到配置
    start = "2023-07-07T10:00:52Z"
    end = "2050-01-01T00:00:00Z"
    return start, end


def make_services(log_path: str):
    registry = RegistryAdapter()
    return {
        "update": UpdateService(registry),
        "defender": DefenderService(registry),
        "onedrive": OneDriveService(registry),
        "version": VersionService(),
        "logs": LogExporter(log_path),
        "firewall": FirewallService(),
    }


def _invoke(action: str, func):
    # NOTE: 编排层统一记录入口与结果，便于区分 UI 事件日志与服务层执行日志
    start = time.perf_counter()
    log_event(logging.INFO, "core_action_started", f"核心调用开始: {action}", action=action, status="started")
    try:
        result = func()
        duration_ms = int((time.perf_counter() - start) * 1000)
        if getattr(result, "ok", False):
            log_event(logging.INFO, "core_action_finished", f"核心调用成功: {action}", action=action, status="ok", duration_ms=duration_ms)
        else:
            err_msg = (getattr(result, "error", None) or {}).get("message", "核心调用失败")
            log_event(
                logging.ERROR,
                "core_action_finished",
                f"核心调用失败: {action}",
                action=action,
                status="failed",
                duration_ms=duration_ms,
                error_type=(getattr(result, "error", None) or {}).get("code", "CORE_ACTION_FAILED"),
                error_message=err_msg,
            )
        return result
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        log_event(
            logging.ERROR,
            "core_action_exception",
            f"核心调用异常: {action} - {e}",
            action=action,
            status="failed",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            exc_info=True,
        )
        raise


def pause_updates(max_days: int = 18300):
    start, end = _default_times()
    services = make_services("")
    return _invoke("pause_updates", lambda: services["update"].pause(max_days, start, end))


def resume_updates():
    services = make_services("")
    return _invoke("resume_updates", lambda: services["update"].resume())


def disable_defender():
    services = make_services("")
    return _invoke("disable_defender", lambda: services["defender"].disable())


def enable_defender():
    services = make_services("")
    return _invoke("enable_defender", lambda: services["defender"].enable())


def disable_onedrive():
    services = make_services("")
    return _invoke("disable_onedrive", lambda: services["onedrive"].disable())


def enable_onedrive():
    services = make_services("")
    return _invoke("enable_onedrive", lambda: services["onedrive"].enable())


def get_version():
    services = make_services("")
    return _invoke("get_version", lambda: services["version"].get_version())


def export_logs(log_path: str, target_path: str):
    services = make_services(log_path)
    return _invoke("export_logs", lambda: services["logs"].export(target_path))


def check_update(current_version: str | None = None):
    # NOTE: 供界面触发的版本比较入口；current_version 不传时使用内置版本号
    services = make_services("")
    return _invoke("check_update", lambda: services["version"].check_update(current_version))


def disable_firewall():
    services = make_services("")
    return _invoke("disable_firewall", lambda: services["firewall"].disable())


def enable_firewall():
    services = make_services("")
    return _invoke("enable_firewall", lambda: services["firewall"].enable())


def pause_updates_with_times(max_days: int, start_iso: str, end_iso: str):
    services = make_services("")
    return _invoke("pause_updates_with_times", lambda: services["update"].pause(max_days, start_iso, end_iso))
