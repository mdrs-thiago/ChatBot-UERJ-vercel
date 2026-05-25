from django.urls import path
from documents.views import (
    AskQuestionView,
    AskRAGView,
    DocumentDeleteView,
    DocumentDetailView,
    DocumentListView,
    DocumentUploadView,
    RAGIndexBuildView,
    ChatUIView,
)
from documents.views_auth import LoginView, LogoutView

urlpatterns = [
    path("update-docs/", RAGIndexBuildView.as_view(), name="update-documents"),
    path("upload/", DocumentUploadView.as_view(), name="upload-document"),
    path(
        "delete/<str:public_id>/", DocumentDeleteView.as_view(), name="delete-document"
    ),
    path("ask/", AskQuestionView.as_view(), name="ask-question"),
    path("ask-all/", AskRAGView.as_view(), name="ask-all-question"),
    path(
        "detail/<str:public_id>/", DocumentDetailView.as_view(), name="detail-document"
    ),
    path("list/", DocumentListView.as_view(), name="list-document"),
    path("chat/", ChatUIView.as_view(), name="chat-ui"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

