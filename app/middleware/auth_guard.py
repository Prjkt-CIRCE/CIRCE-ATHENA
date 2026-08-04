from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC_PATHS = {"/login", "/setup", "/static", "/health"}


class AuthGuard(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Libera rotas públicas
        for public in PUBLIC_PATHS:
            if path.startswith(public):
                return await call_next(request)

        # Verifica sessão
        operator = request.session.get("operator")
        if not operator:
            return RedirectResponse(url="/login", status_code=302)

        return await call_next(request)
