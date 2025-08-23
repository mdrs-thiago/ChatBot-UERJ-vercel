import logging
logger = logging.getLogger(__name__)
"""Middleware to measure and log the execution time of each request."""

import time

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class ExecutionTimeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        start = getattr(request, "_start_time", None)
        if start is not None:
            duration = time.time() - start
            response["X-Execution-Time"] = str(round(duration, 3))
            if isinstance(response, JsonResponse) and hasattr(response, "data"):
                response.data["duration_seconds"] = round(duration, 3)
            logger.info(f"[ExecutionTimeMiddleware] {request.method} {request.path} levou {round(duration, 3)}s")
        return response
