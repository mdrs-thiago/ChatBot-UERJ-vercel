from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.ia_service import answer_question
from documents.models import Document
from documents.serializers import DocumentSerializer, QuestionSerializer, RAGQuestionSerializer

from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document as LCDocument


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
                    description="Quantidade de trechos mais relevantes a considerar (padrão: 3).",
                ),
            },
        ),
        responses={200: "Resposta gerada com sucesso", 400: "Erro na requisição"},
    )
    def post(self, request):
        serializer = RAGQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data["question"]
        top_k = request.data.get("top_k", 3)

        # Buscando todos documentos do banco
        docs_queryset = Document.objects.exclude(content__isnull=True).exclude(content__exact="")
        if not docs_queryset.exists():
            return Response({"error": "Nenhum documento disponível para busca."}, status=400)

        # Convertendo para formato LangChain
        lc_docs = [
            LCDocument(page_content=doc.content, metadata={"title": doc.title, "id": str(doc.public_id)})
            for doc in docs_queryset
        ]

        # Criando embeddings e índice FAISS
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = FAISS.from_documents(lc_docs, embeddings)
        retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": top_k})

        # Buscando contexto relevante
        relevant_docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([d.page_content for d in relevant_docs])

        # LLM gemmini
        answer = answer_question(question, context)

        return Response({
            "question": question,
            "answer": answer,
            "sources": [d.metadata for d in relevant_docs]
        }, status=status.HTTP_200_OK)