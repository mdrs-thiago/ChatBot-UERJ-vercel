from myapi.documents.helpers.chunk_helper import split_juridical_chunks

def test_simple_split():
    text = "Art. 1º Este é o artigo um.\nArt. 2º Este é o artigo dois."
    chunks = split_juridical_chunks(text, max_len=30)
    assert len(chunks) == 2
    assert "Art. 1º" in chunks[0]
    assert "Art. 2º" in chunks[1]


def test_hierarchy():
    text = "CAPÍTULO I\nArt. 1º Texto do artigo.\n§ 1º Parágrafo.\nI – Inciso.\na) Alinea."
    chunks = split_juridical_chunks(text, max_len=50)
    assert any("CAPÍTULO I" in c for c in chunks)
    assert any("Art. 1º" in c for c in chunks)
    assert any("§ 1º" in c for c in chunks)
    assert any("I –" in c for c in chunks)
    assert any("a)" in c for c in chunks)


def test_empty():
    assert split_juridical_chunks("") == []


def test_no_patterns():
    text = "Texto sem padrões jurídicos.\nOutro texto."
    chunks = split_juridical_chunks(text, max_len=20)
    assert len(chunks) >= 1
    assert "Texto sem padrões jurídicos." in chunks[0]
