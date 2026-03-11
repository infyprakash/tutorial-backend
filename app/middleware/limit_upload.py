from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size  # in bytes

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT"):
            body = await request.body()
            if len(body) > self.max_upload_size:
                return Response(
                    content=f"Upload too large. Max {self.max_upload_size / (1024*1024)} MB",
                    status_code=413
                )
        return await call_next(request)