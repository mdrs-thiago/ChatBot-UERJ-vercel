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
    api_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hf_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    conversation_history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        default=list
    )
