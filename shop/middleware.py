import time
import uuid
import logging

# Use dedicated logger named "app"
logger = logging.getLogger("app")


# Middleware that:
# - Generates a unique request ID
# - Measures request duration
# - Adds X-Request-ID header to response
# - Logs one structured line per request
class RequestIdLoggingMiddleware:

    # Django passes the next middleware/view as get_response
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())

        # Attach request_id to request object for later use
        request.request_id = request_id

        # Measure execution time
        start = time.time()
        response = self.get_response(request)
        duration_ms = int((time.time() - start) * 1000)

        # Attach request ID to response header
        # Useful for debugging and tracing
        response["X-Request-ID"] = request_id

        # Log structured information in a single line
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s ip=%s",
            request_id,
            request.method,
            request.path,
            getattr(response, "status_code", "?"),
            duration_ms,
            request.META.get("REMOTE_ADDR", "unknown"),
        )

        return response