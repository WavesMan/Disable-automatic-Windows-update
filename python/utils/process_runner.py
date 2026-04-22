from subprocess import run, PIPE, CalledProcessError
from typing import Tuple
import logging
import time
import traceback

from .logger import log_event


def run_cmd(cmd: str) -> Tuple[bool, str, str]:
    # NOTE: 统一子进程调用，保留 stderr 以便上层进行错误提示与审计；
    #       使用 shell 模式兼容内置 reg 命令，降低对外部依赖的耦合
    start = time.perf_counter()
    try:
        proc = run(cmd, shell=True, check=True, stdout=PIPE, stderr=PIPE, text=True)
        return True, proc.stdout or "", proc.stderr or ""
    except CalledProcessError as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        msg = e.stderr or e.stdout or str(e)
        log_event(
            logging.ERROR,
            "subprocess_failed",
            f"子进程执行失败: {msg}",
            action="run_cmd",
            status="failed",
            cmd=cmd,
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=msg,
        )
        return False, e.stdout or "", e.stderr or ""
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        msg = str(e)
        log_event(
            logging.ERROR,
            "subprocess_exception",
            f"子进程异常: {msg}",
            action="run_cmd",
            status="failed",
            cmd=cmd,
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=msg,
            traceback=traceback.format_exc(),
            exc_info=True,
        )
        return False, "", msg
