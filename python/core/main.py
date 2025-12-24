from ..utils.registry_adapter import RegistryAdapter
from .services import (
    UpdateService,
    DefenderService,
    OneDriveService,
    VersionService,
    LogExporter,
    FirewallService,
)


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


def pause_updates(max_days: int = 18300):
    start, end = _default_times()
    services = make_services("")
    return services["update"].pause(max_days, start, end)


def resume_updates():
    services = make_services("")
    return services["update"].resume()


def disable_defender():
    services = make_services("")
    return services["defender"].disable()


def enable_defender():
    services = make_services("")
    return services["defender"].enable()


def disable_onedrive():
    services = make_services("")
    return services["onedrive"].disable()


def enable_onedrive():
    services = make_services("")
    return services["onedrive"].enable()


def get_version():
    services = make_services("")
    return services["version"].get_version()


def export_logs(log_path: str, target_path: str):
    services = make_services(log_path)
    return services["logs"].export(target_path)


def check_update(current_version: str | None = None):
    # NOTE: 供界面触发的版本比较入口；current_version 不传时使用内置版本号
    services = make_services("")
    return services["version"].check_update(current_version)


def disable_firewall():
    services = make_services("")
    return services["firewall"].disable()


def enable_firewall():
    services = make_services("")
    return services["firewall"].enable()
