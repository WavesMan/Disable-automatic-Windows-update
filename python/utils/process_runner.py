from subprocess import run, PIPE, CalledProcessError
from typing import Tuple


def run_cmd(cmd: str) -> Tuple[bool, str, str]:
    # NOTE: 统一子进程调用，保留 stderr 以便上层进行错误提示与审计；
    #       使用 shell 模式兼容内置 reg 命令，降低对外部依赖的耦合
    try:
        proc = run(cmd, shell=True, check=True, stdout=PIPE, stderr=PIPE, text=True)
        return True, proc.stdout or "", proc.stderr or ""
    except CalledProcessError as e:
        return False, e.stdout or "", e.stderr or ""

