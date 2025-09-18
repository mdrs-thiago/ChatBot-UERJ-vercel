from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

FAISS_INDEX_PATH = "faiss_index"
embeddings = HuggingFaceEmbeddings(model_name=settings.DEFAULT_MODEL)
db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
