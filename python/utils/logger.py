import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

try:
    import ctypes
except Exception:
    ctypes = None


LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "app.log"
MAX_BYTES = 2 * 1024 * 1024
BACKUP_COUNT = 5
_OP_ID: ContextVar[str] = ContextVar("op_id", default="")


class JsonFormatter(logging.Formatter):
    # NOTE: 输出 JSON 行日志，字段固定，便于后续统一采集与检索
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", "log"),
            "action": getattr(record, "action", ""),
            "status": getattr(record, "status", ""),
            "op_id": getattr(record, "op_id", "") or current_op_id(),
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
            "cmd": getattr(record, "cmd", ""),
            "duration_ms": getattr(record, "duration_ms", None),
            "error_type": getattr(record, "error_type", ""),
            "error_message": getattr(record, "error_message", ""),
            "traceback": getattr(record, "traceback", ""),
        }
        if record.exc_info and not data["traceback"]:
            data["traceback"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    # NOTE: 控制台保持可读文本，同时补充 event/op_id 便于现场排障
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        event = getattr(record, "event", "")
        op_id = getattr(record, "op_id", "") or current_op_id()
        suffix = []
        if event:
            suffix.append(f"event={event}")
        if op_id:
            suffix.append(f"op_id={op_id}")
        if suffix:
            return f"{base} [{' '.join(suffix)}]"
        return base


def _resolve_log_dir() -> str:
    # NOTE: 将日志目录置于模块上层路径，避免与源代码同级混淆；同时保证跨模块共享
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, LOG_DIR_NAME)


def new_op_id() -> str:
    return uuid.uuid4().hex[:12]


def current_op_id() -> str:
    return _OP_ID.get()


def set_op_id(op_id: str) -> Token:
    return _OP_ID.set(op_id)


def reset_op_id(token: Token) -> None:
    _OP_ID.reset(token)


def log_event(
    level: int,
    event: str,
    message: str,
    *,
    action: str = "",
    status: str = "",
    op_id: str | None = None,
    cmd: str = "",
    duration_ms: int | None = None,
    error_type: str = "",
    error_message: str = "",
    traceback: str = "",
    exc_info: Any = None,
) -> None:
    # NOTE: 调用方只传语义字段，不感知底层日志处理器实现细节
    payload = {
        "event": event,
        "action": action,
        "status": status,
        "op_id": op_id or current_op_id(),
        "cmd": cmd,
        "duration_ms": duration_ms,
        "error_type": error_type,
        "error_message": error_message,
        "traceback": traceback,
    }
    logging.getLogger().log(level, message, extra=payload, exc_info=exc_info)


def setup_logging() -> str:
    # NOTE: 初始化日志输出，提供路径给上层用于导出与诊断；同时将日志输出到控制台
    log_dir = _resolve_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, LOG_FILE_NAME)
    abs_log_path = os.path.abspath(log_path)

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

    # NOTE: 避免重复添加处理器（支持多次调用）
    has_file = any(
        isinstance(h, RotatingFileHandler) and os.path.abspath(getattr(h, "baseFilename", "")) == abs_log_path
        for h in logger.handlers
    )
    if not has_file:
        fh = RotatingFileHandler(log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(JsonFormatter())
        logger.addHandler(fh)

    has_stream = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers)
    if not has_stream:
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(ConsoleFormatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(sh)

    logger.propagate = False
    log_event(logging.INFO, "app_started", "应用启动", action="startup", status="ok")
    return log_path
