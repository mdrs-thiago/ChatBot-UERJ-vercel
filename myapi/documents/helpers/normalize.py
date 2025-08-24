import unicodedata

def normalize(text):
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()