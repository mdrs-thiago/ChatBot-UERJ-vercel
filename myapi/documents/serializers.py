from documents.models import Document
from rest_framework import serializers


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["public_id", "title", "content", "uploaded_at"]


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    document_id = serializers.CharField()


class RAGQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(required=True)
    top_k = serializers.IntegerField(required=False, min_value=1, default=3)
