from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentSerializer, QuestionSerializer
from .ia_service import answer_question
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status



class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_description="Faz o upload de um documento",
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
            return Response({"error": "Título e arquivo são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)

        content = file.read().decode("utf-8")

        document = Document.objects.create(title=title, content=content)

        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)

class AskQuestionView(APIView):

    @swagger_auto_schema(
        operation_description="Recebe uma pergunta e responde com base no documento especificado.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["question", "document_id"],
            properties={
                "question": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="A pergunta que deseja fazer sobre o documento."
                ),
                "document_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="O ID do documento previamente enviado."
                ),
            },
        ),
        responses={200: "Resposta gerada com sucesso", 400: "Erro na requisição"},
    )
    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            document = get_object_or_404(Document, id=serializer.validated_data["document_id"])
            text = document.content
            
            answer = answer_question(serializer.validated_data["question"], text)
            return Response({"answer": answer})
        
        return Response(serializer.errors, status=400)
