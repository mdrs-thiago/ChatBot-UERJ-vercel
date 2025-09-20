import uuid

from django.db import models


class Document(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LatencyLLM(models.Model):
    provider = models.CharField(max_length=50)
    latency = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)