import functools


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
