import os
from django.conf import settings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import login

login(settings.HUGGINGFACE_HUB_TOKEN)

FAISS_INDEX_PATH = os.path.join(settings.REPO_ROOT, "faiss_index")
embeddings = HuggingFaceEmbeddings(model_name=settings.DEFAULT_MODEL)
db = FAISS.load_local(
    FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
)
