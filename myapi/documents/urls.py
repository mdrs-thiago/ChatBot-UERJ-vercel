from django.urls import path
from .views import DocumentUploadView, AskQuestionView, DocumentDetailView, DocumentListView

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="upload-document"),
    path("ask/", AskQuestionView.as_view(), name="ask-question"),
    path("detail/<str:public_id>/", DocumentDetailView.as_view(), name="detail-document"),
    path("list/", DocumentListView.as_view(), name="list-document"),
]
