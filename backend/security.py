"""Bounded HTTP input and response headers, including rejected requests."""

import asyncio
import time
from starlette.responses import JSONResponse

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
}


class RequestGuard:
    """Buffer at most 11 MiB; do not trust declared lengths or chunk boundaries.

    Bodies have a total 30-second read deadline and at most eight concurrent readers.
    This prototype deliberately runs one worker; limits are process-local.
    """

    def __init__(self, app, max_bytes=11 * 1024 * 1024, read_timeout=30, max_readers=8):
        self.app = app
        self.max_bytes = max_bytes
        self.read_timeout = read_timeout
        self.max_readers = max_readers
        self.readers = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                supplied = {k.lower().encode() for k in SECURITY_HEADERS}
                headers = [(k, v) for k, v in headers if k.lower() not in supplied]
                headers.extend(
                    (k.lower().encode(), v.encode())
                    for k, v in SECURITY_HEADERS.items()
                )
                if scope["path"].startswith("/api"):
                    headers = [
                        (k, v) for k, v in headers if k.lower() != b"cache-control"
                    ]
                    headers.append((b"cache-control", b"no-store"))
                message = {**message, "headers": headers}
            await send(message)

        async def reject(status, detail):
            await JSONResponse({"detail": detail}, status_code=status)(
                scope, receive, secure_send
            )

        if scope["path"].startswith("/api") and scope["method"] not in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            if self.readers >= self.max_readers:
                return await reject(
                    503, "Too many concurrent request bodies; retry shortly"
                )
            chunks = []
            size = 0
            deadline = time.monotonic() + self.read_timeout
            self.readers += 1
            try:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return await reject(408, "Request body timed out")
                    try:
                        message = await asyncio.wait_for(receive(), remaining)
                    except asyncio.TimeoutError:
                        return await reject(408, "Request body timed out")
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    size += len(chunk)
                    if size > self.max_bytes:
                        return await reject(413, "Request body exceeds 11 MB")
                    chunks.append(chunk)
                    if not message.get("more_body", False):
                        break
            finally:
                self.readers -= 1
            payload = b"".join(chunks)
            del chunks
            delivered = False

            async def replay():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": payload, "more_body": False}
                return await receive()

            return await self.app(scope, replay, secure_send)
        return await self.app(scope, receive, secure_send)
