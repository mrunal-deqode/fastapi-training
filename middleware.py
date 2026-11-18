
import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request

from metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_LATENCY

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(request_id)

    start_time = time.perf_counter()
    logger = logging.getLogger("api.request")
    method = request.method
    endpoint = request.url.path

    try:
        logger.info(
            "Request started",
            extra={"method": method, "path": endpoint},
        )

        response = await call_next(request)

        duration = time.perf_counter() - start_time
        status_code = response.status_code

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

        if status_code >= 400:
            ERROR_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code),
            ).inc()

        logger.info(
            "Request completed",
            extra={
                "method": method,
                "path": endpoint,
                "status_code": status_code,
                "duration_seconds": round(duration, 4),
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        duration = time.perf_counter() - start_time

        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status="500",
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

        ERROR_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status="500",
        ).inc()

        logger.exception(
            "Unhandled request exception",
            extra={"method": method, "path": endpoint},
        )
        raise

    finally:
        request_id_var.reset(token)
