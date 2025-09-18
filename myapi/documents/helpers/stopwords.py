import re

from nltk.corpus import stopwords

stop_words = set(stopwords.words("portuguese"))


def remove_stopwords(text):
    """
    Remove as stopwords do texto fornecido.

    Args:
        text (str): A string de entrada da qual as stopwords serão removidas.

    Returns:
        str: O texto sem as stopwords.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    filtered_words = [word for word in words if word not in stop_words]
    return " ".join(filtered_words)
