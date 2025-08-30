from rapidfuzz import process, fuzz
from documents.helpers.normalize import normalize


def syntactic_search(question: str, documents, top_k=5):
    """
    Faz busca sintática (fuzzy matching) sobre os documentos.
    """
    choices = {
        doc.public_id: normalize(doc.content)
        for doc in documents
        if doc.content and doc.content.strip()
    }

    results = process.extract(
        query=question, choices=choices, scorer=fuzz.partial_ratio, limit=top_k
    )

    return results
