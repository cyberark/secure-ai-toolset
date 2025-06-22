import functools
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

def audit_log_operation(audit_logger, handler_name):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(req, *args, **kwargs):
            audit_logger.info(f"Request to {handler_name}: {req!r}")
            result = await func(req, *args, **kwargs)
            audit_logger.info(f"Response from {handler_name}: {result!r}")
            return result

        return wrapper

    return decorator


def get_audit_logger(session_id: str, log_level = logging.INFO) -> logging.Logger:
    file_name = f"agent_guard_core_proxy_{session_id[:5]}.log"
    log_path = Path(f"/logs/{file_name}") if os.access("/logs", os.W_OK) else Path(file_name)
    logger.debug(f"Using audit log path: {log_path}")

    audit_logger = logging.getLogger("agent_guard_core.audit")
    audit_logger.setLevel(log_level)
    audit_logger.propagate = False
    audit_file_handler = logging.FileHandler(log_path)
    audit_file_handler.setLevel(log_level)
    audit_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log_level)
    audit_logger.handlers.clear()
    audit_logger.addHandler(audit_file_handler)

    return audit_logger
