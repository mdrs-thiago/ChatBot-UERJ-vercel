import logging
from django.db import connections
from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Healthcheck da aplicação.
    Retorna 200 se o Django e o banco de dados estiverem acessíveis.
    """

    def get(self, request):
        db_status = "ok"
        try:
            connections["default"].cursor()
        except OperationalError:
            db_status = "fail"

        status_code = (
            status.HTTP_200_OK
            if db_status == "ok"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response({"status": "ok", "database": db_status}, status=status_code)
