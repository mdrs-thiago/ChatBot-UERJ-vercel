import os
import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from documents.ia_service import answer_question
from documents.models import Document
from documents.serializers import (
    DocumentSerializer,
    QuestionSerializer,
    RAGQuestionSerializer,
)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document as LCDocument
from langchain_community.vectorstores import FAISS
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from documents.helpers.chunk_helper import split_juridical_chunks
from documents.helpers.chunk_strategy import get_chunks
from documents.helpers.normalize import normalize

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
        serializer = RAGQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Pergunta inválida recebida: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = normalize(serializer.validated_data["question"])
        top_k = request.data.get("top_k", 5)

        embeddings = HuggingFaceEmbeddings(model_name=settings.DEFAULT_MODEL)

        try:
            db = FAISS.load_local(
                FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
            )
        except Exception as e:
            logger.error(f"Erro ao carregar índice FAISS: {str(e)}")
            return Response(
                {"error": f"Erro ao carregar índice FAISS: {str(e)}"}, status=500
            )
        relevant_docs = db.similarity_search_with_score(question, k=top_k)

        full_docs = []
        for doc, _ in relevant_docs:
            object_of_document = Document.objects.get(public_id=doc.metadata.get("id"))
            full_docs.append(object_of_document)

        full_docs = list(set(full_docs))
        context = "\n\n".join([d.content for d in full_docs])

        answer = answer_question(question, context)

        return Response(
            {
                "question": question,
                "answer": answer,
                "sources": [d.title for d in full_docs],
                "chunks": [dict(d.metadata, score=score) for d, score in relevant_docs],
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

            # Cria o índice FAISS do zero
            db = FAISS.from_documents(lc_docs, embeddings)

            # Salva no disco (pasta criada se não existir)
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
