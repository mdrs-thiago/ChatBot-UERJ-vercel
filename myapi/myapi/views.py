import logging
import os

from django.conf import settings
from django.shortcuts import get_object_or_404
from documents.backend.llm.llm_client import LLMClient
from documents.faiss_loader import db
from documents.helpers.chunk_strategy import get_chunks
from documents.helpers.normalize import normalize
from documents.helpers.stopwords import remove_stopwords
from documents.helpers.syntatic_search import syntactic_search
from documents.ia_service import answer_question
from documents.models import Document
from documents.serializers import (
    DocumentSerializer,
    QuestionSerializer,
    RAGQuestionSerializer,
)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from langchain.schema import Document as LCDocument
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connections
from django.db.utils import OperationalError

FAISS_INDEX_PATH = "faiss_index"
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
