from django.urls import path

from documents.views import (AskQuestionView, DocumentDetailView, DocumentListView, AskRAGView,
                    DocumentUploadView)

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="upload-document"),
    path("ask/", AskQuestionView.as_view(), name="ask-question"),
    path("ask-all/", AskRAGView.as_view(), name="ask-all-question"),
    path(
        "detail/<str:public_id>/", DocumentDetailView.as_view(), name="detail-document"
    ),
    path("list/", DocumentListView.as_view(), name="list-document"),
]
