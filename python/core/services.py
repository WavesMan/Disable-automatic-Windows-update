import json
import os
import urllib.request
import re
import time
import traceback
from dataclasses import dataclass
from typing import Dict, List, Tuple
from ..utils.registry_adapter import RegistryAdapter
from .. import __version__ as PACKAGE_VERSION
from ..utils.process_runner import run_cmd
import logging
from ..utils.logger import log_event


# NOTE: 将键路径集中管理，避免散落在调用处导致维护困难；这些键用于系统策略控制
DEFENDER = r'HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender'
UPDATE = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings'
ONEDRIVE = r'HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\OneDrive'
ONEDRIVE_WIN_POLICY = r'HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\OneDrive'


@dataclass
class Result:
    ok: bool
    data: Dict | None = None
    error: Dict | None = None


class UpdateService:
    # NOTE: 提供暂停/恢复更新的高层接口；时间策略来自配置或默认值，保证幂等调用

    def __init__(self, registry: RegistryAdapter) -> None:
        self.registry = registry

    def pause(self, max_days: int, start_iso: str, end_iso: str) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "update_pause_started", "开始暂停更新", action="pause_updates", status="started")
        cmds = [
            f'reg add "{UPDATE}" /v "FlightSettingsMaxPauseDays" /t REG_DWORD /d {max_days} /f',
            f'reg add "{UPDATE}" /v "PauseFeatureUpdatesStartTime" /t REG_SZ /d "{start_iso}" /f',
            f'reg add "{UPDATE}" /v "PauseFeatureUpdatesEndTime" /t REG_SZ /d "{end_iso}" /f',
            f'reg add "{UPDATE}" /v "PauseQualityUpdatesStartTime" /t REG_SZ /d "{start_iso}" /f',
            f'reg add "{UPDATE}" /v "PauseQualityUpdatesEndTime" /t REG_SZ /d "{end_iso}" /f',
            f'reg add "{UPDATE}" /v "PauseUpdatesStartTime" /t REG_SZ /d "{start_iso}" /f',
            f'reg add "{UPDATE}" /v "PauseUpdatesExpiryTime" /t REG_SZ /d "{end_iso}" /f',
        ]
        ok, errors = self.registry.batch(cmds)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "update_pause_finished", "暂停更新完成", action="pause_updates", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "paused", "effective_until": end_iso})
        log_event(
            logging.ERROR,
            "update_pause_finished",
            "暂停更新失败",
            action="pause_updates",
            status="failed",
            duration_ms=duration_ms,
            error_type="REGISTRY_WRITE_FAILED",
            error_message="; ".join(errors),
        )
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": "部分键写入失败", "details": errors})

    def resume(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "update_resume_started", "开始恢复更新", action="resume_updates", status="started")
        cmds = [
            f'reg delete "{UPDATE}" /v "FlightSettingsMaxPauseDays" /f',
            f'reg delete "{UPDATE}" /v "PauseFeatureUpdatesStartTime" /f',
            f'reg delete "{UPDATE}" /v "PauseFeatureUpdatesEndTime" /f',
            f'reg delete "{UPDATE}" /v "PauseQualityUpdatesStartTime" /f',
            f'reg delete "{UPDATE}" /v "PauseQualityUpdatesEndTime" /f',
            f'reg delete "{UPDATE}" /v "PauseUpdatesStartTime" /f',
            f'reg delete "{UPDATE}" /v "PauseUpdatesExpiryTime" /f',
        ]
        ok, errors = self.registry.batch(cmds)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "update_resume_finished", "恢复更新完成", action="resume_updates", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "resumed"})
        log_event(
            logging.ERROR,
            "update_resume_finished",
            "恢复更新失败",
            action="resume_updates",
            status="failed",
            duration_ms=duration_ms,
            error_type="REGISTRY_DELETE_FAILED",
            error_message="; ".join(errors),
        )
        return Result(False, error={"code": "REGISTRY_DELETE_FAILED", "message": "部分键删除失败", "details": errors})


class DefenderService:
    # NOTE: 统一管理防护软件策略位，避免 UI 直接操作敏感键

    def __init__(self, registry: RegistryAdapter) -> None:
        self.registry = registry

    def disable(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "defender_disable_started", "开始禁用 Defender", action="disable_defender", status="started")
        ok, msg = self.registry.add_dword(DEFENDER, "DisableAntiSpyware", 1)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "defender_disable_finished", "禁用 Defender 成功", action="disable_defender", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "disabled"})
        log_event(
            logging.ERROR,
            "defender_disable_finished",
            f"禁用 Defender 失败: {msg}",
            action="disable_defender",
            status="failed",
            duration_ms=duration_ms,
            error_type="REGISTRY_WRITE_FAILED",
            error_message=msg,
        )
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": msg})

    def enable(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "defender_enable_started", "开始启用 Defender", action="enable_defender", status="started")
        ok, msg = self.registry.add_dword(DEFENDER, "DisableAntiSpyware", 0)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "defender_enable_finished", "启用 Defender 成功", action="enable_defender", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "enabled"})
        log_event(
            logging.ERROR,
            "defender_enable_finished",
            f"启用 Defender 失败: {msg}",
            action="enable_defender",
            status="failed",
            duration_ms=duration_ms,
            error_type="REGISTRY_WRITE_FAILED",
            error_message=msg,
        )
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": msg})


class OneDriveService:
    # NOTE: 统一管理云盘同步开关，减少键值误写的风险

    def __init__(self, registry: RegistryAdapter) -> None:
        self.registry = registry

    def disable(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "onedrive_disable_started", "开始禁用 OneDrive", action="disable_onedrive", status="started")
        # NOTE: 采用组策略键的双路径写入提高可靠性，并移除当前用户自启动项，减少自动拉起；
        #       同时尝试结束相关进程（若不存在则容错忽略）
        cmds = [
            'taskkill /F /IM OneDrive.exe',
            'taskkill /F /IM OneDriveStandaloneUpdater.exe',
            f'reg add "{ONEDRIVE}" /v "DisableFileSyncNGSC" /t REG_DWORD /d 1 /f',
            f'reg add "{ONEDRIVE_WIN_POLICY}" /v "DisableFileSync" /t REG_DWORD /d 1 /f',
            'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "OneDrive" /f',
        ]
        ok, errors = self.registry.batch(cmds)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "onedrive_disable_finished", "禁用 OneDrive 成功", action="disable_onedrive", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "disabled"})
        log_event(
            logging.ERROR,
            "onedrive_disable_finished",
            "禁用 OneDrive 失败",
            action="disable_onedrive",
            status="failed",
            duration_ms=duration_ms,
            error_type="REGISTRY_WRITE_FAILED",
            error_message="; ".join(errors),
        )
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": "部分键写入失败", "details": errors})

    def enable(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "onedrive_enable_started", "开始启用 OneDrive", action="enable_onedrive", status="started")
        cmds = [
            f'reg add "{ONEDRIVE}" /v "DisableFileSyncNGSC" /t REG_DWORD /d 0 /f',
            f'reg add "{ONEDRIVE_WIN_POLICY}" /v "DisableFileSync" /t REG_DWORD /d 0 /f',
        ]
        ok, errors = self.registry.batch(cmds)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "onedrive_enable_finished", "启用 OneDrive 成功", action="enable_onedrive", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "enabled"})
        log_event(
            logging.ERROR,
            "onedrive_enable_finished",
            "启用 OneDrive 失败",
            action="enable_onedrive",
            status="failed",
            duration_ms=duration_ms,
            error_type="REGISTRY_WRITE_FAILED",
            error_message="; ".join(errors),
        )
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": "部分键写入失败", "details": errors})


class VersionService:
    # NOTE: 版本信息获取受网络与服务端限流影响，需提供简易降级；此处先直接请求，后续可加缓存

    RELEASES_URL = 'https://api.github.com/repos/WavesMan/Disable-automatic-Windows-update/releases'
    RELEASE_PAGE = 'https://github.com/WavesMan/Disable-automatic-Windows-update/releases'
    CURRENT_VERSION = PACKAGE_VERSION

    def get_version(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "version_get_started", "开始获取版本信息", action="get_version", status="started")
        try:
            req = urllib.request.Request(self.RELEASES_URL)
            req.add_header('User-Agent', 'Python/3.13')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                releases = [r for r in data if r.get("tag_name", "").startswith("EXE-")]
                ver = releases[0]["tag_name"] if releases else "无版本"
                duration_ms = int((time.perf_counter() - start) * 1000)
                log_event(logging.INFO, "version_get_finished", "获取版本信息成功", action="get_version", status="ok", duration_ms=duration_ms)
                return Result(True, data={"version": ver, "source": "github"})
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            log_event(
                logging.ERROR,
                "version_get_finished",
                f"获取版本信息失败: {e}",
                action="get_version",
                status="failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                exc_info=True,
            )
            return Result(False, error={"code": "NETWORK_ERROR", "message": str(e)})

    def _normalize(self, tag: str) -> str:
        s = (tag or "").strip()
        if s.startswith("EXE-"):
            s = s[4:]
        if s[:1].lower() == "v":
            s = s[1:]
        return s

    def _parse_nums(self, s: str) -> list[int]:
        s = self._normalize(s)
        nums = re.findall(r"\d+", s)
        return [int(n) for n in nums] if nums else []

    def _cmp(self, a: str, b: str) -> int:
        na = self._parse_nums(a)
        nb = self._parse_nums(b)
        if na and nb:
            L = max(len(na), len(nb))
            for i in range(L):
                va = na[i] if i < len(na) else 0
                vb = nb[i] if i < len(nb) else 0
                if va < vb:
                    return -1
                if va > vb:
                    return 1
            return 0
        if not na and nb:
            return -1
        if na and not nb:
            return 1
        return 0

    def check_update(self, current_version: str | None = None) -> Result:
        cur = current_version or self.CURRENT_VERSION
        start = time.perf_counter()
        log_event(logging.INFO, "version_check_started", "开始检查更新", action="check_update", status="started")
        try:
            req = urllib.request.Request(self.RELEASES_URL)
            req.add_header('User-Agent', 'Python/3.13')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                releases = [r for r in data if r.get("tag_name", "").startswith("EXE-")]
                latest = releases[0]["tag_name"] if releases else "无版本"
                cmp = self._cmp(cur, latest) if latest != "无版本" else 0
                has_update = (cmp < 0)
                duration_ms = int((time.perf_counter() - start) * 1000)
                log_event(
                    logging.INFO,
                    "version_check_finished",
                    "检查更新完成",
                    action="check_update",
                    status="ok",
                    duration_ms=duration_ms,
                    error_message=(f"has_update={has_update}"),
                )
                return Result(
                    True,
                    data={
                        "current": cur,
                        "latest": latest,
                        "has_update": has_update,
                        "release_url": self.RELEASE_PAGE,
                    },
                )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            log_event(
                logging.ERROR,
                "version_check_finished",
                f"检查更新失败: {e}",
                action="check_update",
                status="failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                exc_info=True,
            )
            return Result(False, error={"code": "NETWORK_ERROR", "message": str(e)})


class LogExporter:
    # NOTE: 日志导出涉及用户文件系统，需避免覆盖与路径错误；此处留给上层选择目标路径

    def __init__(self, log_path: str) -> None:
        self.log_path = log_path

    def export(self, target_path: str) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "logs_export_started", "开始导出日志", action="export_logs", status="started", error_message=target_path)
        if not os.path.exists(self.log_path):
            # NOTE: 为兼容旧实现，尝试回退到历史路径 python/logs/app.log
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            legacy_path = os.path.join(repo_root, "python", "logs", "app.log")
            candidate = legacy_path if os.path.exists(legacy_path) else None
            if not candidate:
                duration_ms = int((time.perf_counter() - start) * 1000)
                log_event(
                    logging.ERROR,
                    "logs_export_finished",
                    "导出日志失败: 未找到日志文件",
                    action="export_logs",
                    status="failed",
                    duration_ms=duration_ms,
                    error_type="NOT_FOUND",
                    error_message="未找到日志文件",
                )
                return Result(False, error={"code": "NOT_FOUND", "message": "未找到日志文件"})
            self.log_path = candidate
        try:
            with open(self.log_path, "rb") as src, open(target_path, "wb") as dst:
                data = src.read()
                dst.write(data)
            duration_ms = int((time.perf_counter() - start) * 1000)
            log_event(logging.INFO, "logs_export_finished", "导出日志成功", action="export_logs", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "ok", "bytes": len(data)})
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            log_event(
                logging.ERROR,
                "logs_export_finished",
                f"导出日志失败: {e}",
                action="export_logs",
                status="failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                exc_info=True,
            )
            return Result(False, error={"code": "FILE_EXPORT_FAILED", "message": str(e)})


class FirewallService:
    # NOTE: 使用 netsh 控制所有防火墙配置文件开关，提高跨版本兼容性

    def _batch(self, cmds: List[str]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        for cmd in cmds:
            step_start = time.perf_counter()
            log_event(logging.INFO, "firewall_command_started", "执行命令", action="firewall_command", status="started", cmd=cmd)
            ok, out, err = run_cmd(cmd)
            duration_ms = int((time.perf_counter() - step_start) * 1000)
            if ok:
                log_event(logging.INFO, "firewall_command_finished", "执行成功", action="firewall_command", status="ok", cmd=cmd, duration_ms=duration_ms)
            else:
                msg = err or out or "执行失败"
                log_event(
                    logging.ERROR,
                    "firewall_command_finished",
                    f"执行失败: {msg}",
                    action="firewall_command",
                    status="failed",
                    cmd=cmd,
                    duration_ms=duration_ms,
                    error_type="CommandFailed",
                    error_message=msg,
                )
                errors.append(msg)
        return (len(errors) == 0), errors

    def disable(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "firewall_disable_started", "开始停用防火墙", action="disable_firewall", status="started")
        cmds = [
            "netsh advfirewall set allprofiles state off",
            "netsh advfirewall set domainprofile state off",
            "netsh advfirewall set privateprofile state off",
            "netsh advfirewall set publicprofile state off",
        ]
        ok, errors = self._batch(cmds)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "firewall_disable_finished", "停用防火墙成功", action="disable_firewall", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "firewall_disabled"})
        log_event(
            logging.ERROR,
            "firewall_disable_finished",
            "停用防火墙失败",
            action="disable_firewall",
            status="failed",
            duration_ms=duration_ms,
            error_type="FIREWALL_DISABLE_FAILED",
            error_message="; ".join(errors),
        )
        return Result(False, error={"code": "FIREWALL_DISABLE_FAILED", "message": "防火墙停用失败", "details": errors})

    def enable(self) -> Result:
        start = time.perf_counter()
        log_event(logging.INFO, "firewall_enable_started", "开始恢复防火墙", action="enable_firewall", status="started")
        cmds = [
            "netsh advfirewall set allprofiles state on",
            "netsh advfirewall set domainprofile state on",
            "netsh advfirewall set privateprofile state on",
            "netsh advfirewall set publicprofile state on",
        ]
        ok, errors = self._batch(cmds)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if ok:
            log_event(logging.INFO, "firewall_enable_finished", "恢复防火墙成功", action="enable_firewall", status="ok", duration_ms=duration_ms)
            return Result(True, data={"status": "firewall_enabled"})
        log_event(
            logging.ERROR,
            "firewall_enable_finished",
            "恢复防火墙失败",
            action="enable_firewall",
            status="failed",
            duration_ms=duration_ms,
            error_type="FIREWALL_ENABLE_FAILED",
            error_message="; ".join(errors),
        )
        return Result(False, error={"code": "FIREWALL_ENABLE_FAILED", "message": "防火墙恢复失败", "details": errors})
