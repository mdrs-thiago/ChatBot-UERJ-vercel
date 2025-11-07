from django.conf import settings
from documents.helpers.normalize import normalize
from rapidfuzz import fuzz, process


def syntactic_search(question: str, documents, top_k=5):
    """
    Faz busca sintática (fuzzy matching) sobre os documentos.
    """
    choices = {
        doc.public_id: normalize(doc.content).lower()
        for doc in documents
        if doc.content and doc.content.strip()
    }

    results = process.extract(
        query=question, choices=choices, scorer=fuzz.partial_ratio, limit=top_k
    )

    filtered_results = [r for r in results if r[1] >= settings.SYNTATIC_SCORE_THRESHOLD]
    if filtered_results:
        return filtered_results
    return results
