# myapp/middleware/api_key_middleware.py

import os
from django.http import JsonResponse


class APIKeyMiddleware:
    """
    Middleware para autenticação via X-API-KEY.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.API_KEY = os.getenv("API_KEY", "minha_chave_teste")

    def __call__(self, request):
        public_paths = ["/admin", "/health", '/swagger', '/api/chat/', '/api/login/', '/api/logout/', '/favicon.ico']
        if any(request.path.startswith(p) for p in public_paths):
            return self.get_response(request)

        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return JsonResponse({"error": "X-API-KEY ausente"}, status=401)

        if api_key != self.API_KEY:
            return JsonResponse({"error": "X-API-KEY inválida"}, status=403)

        response = self.get_response(request)
        return response
