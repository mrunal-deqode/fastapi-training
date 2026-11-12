import time
from fastapi import Request


async def logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    print(f"Request:{request.method}{request.url.path} | ",
          f"Status:{response.status_code} | ", f"Processing time:{process_time:.4f}seconds")

    return response
