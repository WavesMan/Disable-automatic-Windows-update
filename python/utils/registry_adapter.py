from typing import List, Tuple
import logging

from .process_runner import run_cmd


def _wrap_result(ok: bool, stdout: str, stderr: str) -> Tuple[bool, str]:
    # NOTE: 上层只关心是否成功与可读错误信息，这里做轻度归一化，避免 UI 直接暴露底层命令细节
    if ok:
        return True, ""
    return False, (stderr or stdout or "执行失败")


class RegistryAdapter:
    # NOTE: 将具体 reg 命令封装为声明式接口，避免调用方拼接字符串带来易错与不可维护问题

    def execute(self, cmd: str) -> Tuple[bool, str]:
        logging.info(f"执行命令: {cmd}")
        ok, out, err = run_cmd(cmd)
        ok2, msg = _wrap_result(ok, out, err)

        # NOTE: 容错处理：删除不存在的注册表项或结束不存在的进程视为成功，提升整体可靠性
        low_cmd = cmd.lower().strip()
        low_msg = (msg or "").lower()
        if not ok2:
            if low_cmd.startswith("reg delete") and (
                "unable to find the specified registry key or value" in low_msg
                or "系统找不到指定的注册表项或值" in low_msg
            ):
                logging.info("目标注册表项不存在，视为已删除")
                ok2, msg = True, ""
            elif low_cmd.startswith("taskkill") and (
                "not found" in low_msg or "no instance" in low_msg or "找不到" in low_msg
            ):
                logging.info("目标进程不存在，视为已结束")
                ok2, msg = True, ""

        if ok2:
            logging.info("执行成功")
        else:
            logging.error(f"执行失败: {msg}")
        return ok2, msg

    def batch(self, cmds: List[str]) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        for cmd in cmds:
            ok, msg = self.execute(cmd)
            if not ok:
                errors.append(msg)
        return (len(errors) == 0), errors

    def add_dword(self, key_path: str, name: str, value: int) -> Tuple[bool, str]:
        cmd = f'reg add "{key_path}" /v "{name}" /t REG_DWORD /d {value} /f'
        return self.execute(cmd)

    def add_sz(self, key_path: str, name: str, value: str) -> Tuple[bool, str]:
        cmd = f'reg add "{key_path}" /v "{name}" /t REG_SZ /d "{value}" /f'
        return self.execute(cmd)

    def delete_value(self, key_path: str, name: str) -> Tuple[bool, str]:
        cmd = f'reg delete "{key_path}" /v "{name}" /f'
        return self.execute(cmd)
