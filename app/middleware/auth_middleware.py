import jwt
import datetime as dt
from fastapi import HTTPException, Request, logger
from decouple import config
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from app.models.user import User

SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
SKIP_PATHS = ["/auth/google","/auth/google/", "/auth/google/callback", "/docs", "/openapi.json", "/"]

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app,):
        super().__init__(app)

    async def _is_authorized(self, token: str) -> bool:
        with open("./.allowed_users", 'r') as allowed_users_file:
            lines = allowed_users_file.readlines()
            allowed_users = [line.strip() for line in lines]
        try:
            payload = jwt.decode(token, str(SECRET_KEY), algorithms=[str(ALGORITHM)])
            user = User(**payload)
            if user.email is None or user.email not in allowed_users:
                logger.logger.info("User tried making request. Unauthorized.", extra={"email": user.email})
                return False
            
            return True
        except Exception as e:
            logger.logger.info("User tried making request. Unauthorized.", extra={"error": e})
            return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authorization for certain paths
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        # Extract token from the Authorization header
        token = request.cookies.get("Authorization", "").replace("Bearer ", "")

        # Check if the token is authorized
        if not await self._is_authorized(token):
            raise HTTPException(status_code=401, detail="Unauthorized")

        return await call_next(request)
