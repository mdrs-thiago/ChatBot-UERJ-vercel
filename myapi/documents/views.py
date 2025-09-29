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
from documents.helpers.resolution_search import normalize_resolution
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

FAISS_INDEX_PATH = "faiss_index"
logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Faz o upload de um documento",
        tags=["Document"],
        manual_parameters=[
            openapi.Parameter(
                name="title",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="Título do documento",
                required=True,
            ),
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Arquivo para upload",
                required=True,
            ),
        ],
        responses={201: "Documento criado com sucesso", 400: "Erro nos dados enviados"},
    )
    def post(self, request, *args, **kwargs):
        title = request.data.get("title")
        file = request.FILES.get("file")

        if not file or not title:
            return Response(
                {"error": "Título e arquivo são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content = file.read().decode("utf-8")

        document = Document.objects.create(title=title, content=content)

        return Response(
            DocumentSerializer(document).data, status=status.HTTP_201_CREATED
        )


class AskQuestionView(APIView):

    @swagger_auto_schema(
        operation_description="Recebe uma pergunta e responde com base no documento especificado.",
        tags=["Document"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["question", "document_id"],
            properties={
                "question": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="A pergunta que deseja fazer sobre o documento.",
                ),
                "document_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="O ID do documento previamente enviado.",
                ),
            },
        ),
        responses={200: "Resposta gerada com sucesso", 400: "Erro na requisição"},
    )
    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            document = get_object_or_404(
                Document, public_id=serializer.validated_data["document_id"]
            )
            text = document.content

            answer = answer_question(serializer.validated_data["question"], text)
            return Response({"answer": answer})

        return Response(serializer.errors, status=400)


class DocumentListView(APIView):
    """
    Retorna todos os documentos salvos no banco.
    """

    @swagger_auto_schema(
        operation_description="Lista todos os documentos.",
        tags=["Document"],
        responses={200: DocumentSerializer(many=True)},
    )
    def get(self, request):
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentDetailView(APIView):
    """
    Retorna um único documento pelo ID.
    """

    @swagger_auto_schema(
        operation_description="Obtém um documento pelo ID.",
        tags=["Document"],
        manual_parameters=[
            openapi.Parameter(
                "public_id",
                openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="ID do Documento",
            )
        ],
        responses={200: DocumentSerializer(), 404: "Documento não encontrado"},
    )
    def get(self, request, public_id):
        document = get_object_or_404(Document, public_id=public_id)
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AskRAGView(APIView):
    """
    Recebe uma pergunta e busca a resposta usando RAG
    com base em todos os documentos armazenados.
    """

    @swagger_auto_schema(
        operation_description="Pergunta usando RAG com base nos documentos salvos.",
        tags=["Document"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["question"],
            properties={
                "question": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Pergunta a ser respondida usando os documentos.",
                ),
                "top_k": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Quantidade de trechos mais relevantes a considerar (padrão: 5).",
                ),
            },
        ),
        responses={200: "Resposta gerada com sucesso", 400: "Erro na requisição"},
    )
    def post(self, request):
        logger.info(f"[AskRAGView][post] - Informações recebidas: {request.data}")
        full_docs = []

        serializer = RAGQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Pergunta inválida recebida: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        top_k = request.data.get("top_k", 5)

        docs_queryset = Document.objects.exclude(content__isnull=True).exclude(
            content__exact=""
        )
        question = normalize(serializer.validated_data["question"])
        clean_question = remove_stopwords(question)
        resolution = normalize_resolution(serializer.validated_data["question"])
        if resolution and settings.FEATURE_FLAG_ENABLE_RESOLUTION_SEARCH:
            logger.info(f"[AskRAGView][post] - Resolution find: {resolution}")
            clean_question = resolution
        results = syntactic_search(clean_question, docs_queryset, top_k=top_k)
        for _, _, public_id in results:
            object_of_document = Document.objects.get(public_id=public_id)
            full_docs.append(object_of_document)

        logger.info(
            f"[AskRAGView][post] - finish syntactic_search with {len(results)} results"
        )

        relevant_docs = db.similarity_search_with_score(question, k=top_k)
        logger.info(
            f"[AskRAGView][post] - finish similarity_search_with_score {len(relevant_docs)} results"
        )

        docs_to_use = relevant_docs
        filtered_relevant_docs = [
            (doc, score)
            for doc, score in relevant_docs
            if score * 100 >= settings.SEMANTIC_SCORE_THRESHOLD
        ]
        if filtered_relevant_docs:
            docs_to_use = filtered_relevant_docs

        for doc, _ in docs_to_use:
            object_of_document = Document.objects.get(public_id=doc.metadata.get("id"))
            full_docs.append(object_of_document)

        full_docs = list(set(full_docs))

        context = "\n\n".join([d.content for d in full_docs])

        logger.info(f"[AskRAGView][post] - start LLM with {len(full_docs)} docs")

        client = LLMClient(
            model_name=settings.DEFAULT_MODEL_NAME_PROVIDER,
            provider=settings.DEFAULT_PROVIDER,
        )
        dict_answer = client.generate(question, context)

        return Response(
            {
                "question": question,
                "answer": dict_answer.get("answer"),
                "metrics": dict_answer.get("metrics", {}),
                "sources": [d.title for d in full_docs],
                "semantic_search": [
                    dict(d.metadata, score=score) for d, score in relevant_docs
                ],
                "syntactic_search": [
                    {"id": index, "score": score} for _, score, index in results
                ],
            },
            status=200,
        )


class RAGIndexBuildView(APIView):
    @swagger_auto_schema(
        operation_summary="(Re)cria o índice FAISS com todos os documentos",
        operation_description="Busca todos os documentos no banco, gera embeddings, cria ou atualiza o índice FAISS, e salva no disco.",
        responses={
            200: openapi.Response(description="Índice criado/atualizado com sucesso."),
            400: openapi.Response(
                description="Nenhum documento disponível para indexação."
            ),
            500: openapi.Response(description="Erro ao criar o índice."),
        },
        tags=["Document"],
    )
    def post(self, request):
        try:
            docs_queryset = Document.objects.exclude(content__isnull=True).exclude(
                content__exact=""
            )
            if not docs_queryset.exists():
                return Response(
                    {"error": "Nenhum documento disponível para indexação."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            lc_docs = []
            for doc in docs_queryset:
                chunks = get_chunks(doc.content)
                for i, chunk in enumerate(chunks):
                    lc_docs.append(
                        LCDocument(
                            page_content=normalize(chunk),
                            metadata={
                                "title": doc.title,
                                "id": str(doc.public_id),
                                "chunk_id": i,
                                "text_chunk": chunk,
                            },
                        )
                    )

            embeddings = HuggingFaceEmbeddings(model_name=settings.DEFAULT_MODEL)

            db = FAISS.from_documents(lc_docs, embeddings)

            os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
            db.save_local(FAISS_INDEX_PATH)

            return Response({"message": "Índice FAISS criado/atualizado com sucesso."})

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDeleteView(APIView):
    @swagger_auto_schema(
        operation_summary="Deleta documento com base no public_id",
        operation_description="Procura o documento no banco com base no public_id e deleta.",
        responses={
            204: openapi.Response(description="Documento deletado com sucesso."),
            404: openapi.Response(description="Nenhum documento encontrado."),
        },
        tags=["Document"],
    )
    def delete(self, request, public_id):
        document = get_object_or_404(Document, public_id=public_id)
        document.delete()
        return Response(
            {"message": "Documento deletado com sucesso."},
            status=status.HTTP_204_NO_CONTENT,
        )
