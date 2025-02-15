from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["public_id", "title", "content", "uploaded_at"]

class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    document_id = serializers.IntegerField()
