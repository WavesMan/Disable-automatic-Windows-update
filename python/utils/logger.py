import logging
import os
import sys
try:
    import ctypes
except Exception:
    ctypes = None


LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "app.log"


def _resolve_log_dir() -> str:
    # NOTE: 将日志目录置于模块上层路径，避免与源代码同级混淆；同时保证跨模块共享
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, LOG_DIR_NAME)


def setup_logging() -> str:
    # NOTE: 初始化日志输出，提供路径给上层用于导出与诊断；同时将日志输出到控制台
    log_dir = _resolve_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, LOG_FILE_NAME)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # NOTE: 统一控制台编码为 UTF-8，避免中文输出出现乱码
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    try:
        if ctypes is not None:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass

    # 避免重复添加处理器（支持多次调用）
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(sh)

    logger.propagate = False

    logger.info("应用启动")
    return log_path
