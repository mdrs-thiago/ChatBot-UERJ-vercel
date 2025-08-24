from myapi.documents.helpers.normalize import normalize

def test_ascii():
    assert normalize("abcABC123") == "abcABC123"

def test_accented():
    assert normalize("áéíóúçãõ") == "aeioucao"
    assert normalize("ÀÊÎÔÛ") == "AEIOU"

def test_mixed():
    assert normalize("Olá, João!") == "Ola, Joao!"

def test_symbols():
    assert normalize("@#%$&*()") == "@#%$&*()"

def test_empty():
    assert normalize("") == ""
