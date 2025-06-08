import functools
import logging
import logging.handlers


def get_audit_logger()-> logging.Logger:
    global formatter
    audit_logger = logging.getLogger("agent_guard_core.audit")
    audit_logger.setLevel(logging.DEBUG)
    sys_log = logging.handlers.SysLogHandler()
    audit_file_handler = logging.FileHandler("agent_guard_core_proxy.log")
    audit_file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    audit_file_handler.setFormatter(formatter)
    if not audit_logger.hasHandlers():
        audit_logger.addHandler(audit_file_handler)
        audit_logger.addHandler(sys_log)

    return audit_logger

def audit_log_handler(audit_logger, handler_name):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(req, *args, **kwargs):
            audit_logger.info(f"Request to {handler_name}: {req!r}")
            result = await func(req, *args, **kwargs)
            audit_logger.info(f"Response from {handler_name}: {result!r}")
            return result
        return wrapper
    return decorator
