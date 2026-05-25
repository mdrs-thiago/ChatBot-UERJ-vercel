import os
from django.conf import settings
from langchain_community.vectorstores import FAISS
from documents.helpers.gemini_embeddings import GeminiEmbeddings

FAISS_INDEX_PATH = os.path.join(settings.REPO_ROOT, "faiss_index")
embeddings = GeminiEmbeddings()
db = FAISS.load_local(
    FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
)
