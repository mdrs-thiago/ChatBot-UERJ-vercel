from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentSerializer, QuestionSerializer
from .ia_service import answer_question
import os

class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AskQuestionView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            document = get_object_or_404(Document, id=serializer.validated_data["document_id"])
            
            file_path = os.path.join(os.path.dirname(__file__), document.file.path)
            
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()
            
            answer = answer_question(serializer.validated_data["question"], text)
            return Response({"answer": answer})
        
        return Response(serializer.errors, status=400)
