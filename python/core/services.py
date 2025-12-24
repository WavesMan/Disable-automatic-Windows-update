import json
import os
import urllib.request
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
from ..utils.registry_adapter import RegistryAdapter
from .. import __version__ as PACKAGE_VERSION
from ..utils.process_runner import run_cmd
import logging


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
        if ok:
            return Result(True, data={"status": "paused", "effective_until": end_iso})
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": "部分键写入失败", "details": errors})

    def resume(self) -> Result:
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
        if ok:
            return Result(True, data={"status": "resumed"})
        return Result(False, error={"code": "REGISTRY_DELETE_FAILED", "message": "部分键删除失败", "details": errors})


class DefenderService:
    # NOTE: 统一管理防护软件策略位，避免 UI 直接操作敏感键

    def __init__(self, registry: RegistryAdapter) -> None:
        self.registry = registry

    def disable(self) -> Result:
        ok, msg = self.registry.add_dword(DEFENDER, "DisableAntiSpyware", 1)
        if ok:
            return Result(True, data={"status": "disabled"})
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": msg})

    def enable(self) -> Result:
        ok, msg = self.registry.add_dword(DEFENDER, "DisableAntiSpyware", 0)
        if ok:
            return Result(True, data={"status": "enabled"})
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": msg})


class OneDriveService:
    # NOTE: 统一管理云盘同步开关，减少键值误写的风险

    def __init__(self, registry: RegistryAdapter) -> None:
        self.registry = registry

    def disable(self) -> Result:
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
        if ok:
            return Result(True, data={"status": "disabled"})
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": "部分键写入失败", "details": errors})

    def enable(self) -> Result:
        cmds = [
            f'reg add "{ONEDRIVE}" /v "DisableFileSyncNGSC" /t REG_DWORD /d 0 /f',
            f'reg add "{ONEDRIVE_WIN_POLICY}" /v "DisableFileSync" /t REG_DWORD /d 0 /f',
        ]
        ok, errors = self.registry.batch(cmds)
        if ok:
            return Result(True, data={"status": "enabled"})
        return Result(False, error={"code": "REGISTRY_WRITE_FAILED", "message": "部分键写入失败", "details": errors})


class VersionService:
    # NOTE: 版本信息获取受网络与服务端限流影响，需提供简易降级；此处先直接请求，后续可加缓存

    RELEASES_URL = 'https://api.github.com/repos/WavesMan/Disable-automatic-Windows-update/releases'
    RELEASE_PAGE = 'https://github.com/WavesMan/Disable-automatic-Windows-update/releases'
    CURRENT_VERSION = PACKAGE_VERSION

    def get_version(self) -> Result:
        try:
            req = urllib.request.Request(self.RELEASES_URL)
            req.add_header('User-Agent', 'Python/3.13')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                releases = [r for r in data if r.get("tag_name", "").startswith("EXE-")]
                ver = releases[0]["tag_name"] if releases else "无版本"
                return Result(True, data={"version": ver, "source": "github"})
        except Exception as e:
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
        try:
            req = urllib.request.Request(self.RELEASES_URL)
            req.add_header('User-Agent', 'Python/3.13')
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                releases = [r for r in data if r.get("tag_name", "").startswith("EXE-")]
                latest = releases[0]["tag_name"] if releases else "无版本"
                cmp = self._cmp(cur, latest) if latest != "无版本" else 0
                has_update = (cmp < 0)
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
            return Result(False, error={"code": "NETWORK_ERROR", "message": str(e)})


class LogExporter:
    # NOTE: 日志导出涉及用户文件系统，需避免覆盖与路径错误；此处留给上层选择目标路径

    def __init__(self, log_path: str) -> None:
        self.log_path = log_path

    def export(self, target_path: str) -> Result:
        if not os.path.exists(self.log_path):
            # NOTE: 为兼容旧实现，尝试回退到历史路径 python/logs/app.log
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            legacy_path = os.path.join(repo_root, "python", "logs", "app.log")
            candidate = legacy_path if os.path.exists(legacy_path) else None
            if not candidate:
                return Result(False, error={"code": "NOT_FOUND", "message": "未找到日志文件"})
            self.log_path = candidate
        try:
            with open(self.log_path, "rb") as src, open(target_path, "wb") as dst:
                data = src.read()
                dst.write(data)
            return Result(True, data={"status": "ok", "bytes": len(data)})
        except Exception as e:
            return Result(False, error={"code": "FILE_EXPORT_FAILED", "message": str(e)})


class FirewallService:
    # NOTE: 使用 netsh 控制所有防火墙配置文件开关，提高跨版本兼容性

    def _batch(self, cmds: List[str]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        for cmd in cmds:
            logging.info(f"执行命令: {cmd}")
            ok, out, err = run_cmd(cmd)
            if ok:
                logging.info("执行成功")
            else:
                msg = err or out or "执行失败"
                logging.error(f"执行失败: {msg}")
                errors.append(msg)
        return (len(errors) == 0), errors

    def disable(self) -> Result:
        cmds = [
            "netsh advfirewall set allprofiles state off",
            "netsh advfirewall set domainprofile state off",
            "netsh advfirewall set privateprofile state off",
            "netsh advfirewall set publicprofile state off",
        ]
        ok, errors = self._batch(cmds)
        if ok:
            return Result(True, data={"status": "firewall_disabled"})
        return Result(False, error={"code": "FIREWALL_DISABLE_FAILED", "message": "防火墙停用失败", "details": errors})

    def enable(self) -> Result:
        cmds = [
            "netsh advfirewall set allprofiles state on",
            "netsh advfirewall set domainprofile state on",
            "netsh advfirewall set privateprofile state on",
            "netsh advfirewall set publicprofile state on",
        ]
        ok, errors = self._batch(cmds)
        if ok:
            return Result(True, data={"status": "firewall_enabled"})
        return Result(False, error={"code": "FIREWALL_ENABLE_FAILED", "message": "防火墙恢复失败", "details": errors})
