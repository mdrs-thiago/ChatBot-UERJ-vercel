import os
from documents.helpers.chunk_helper import split_juridical_chunks
from langchain.text_splitter import RecursiveCharacterTextSplitter


def get_chunks(doc_content):
    strategy = os.getenv("CHUNK_STRATEGY", "own")
    if strategy == "split_juridical_chunks":
        return split_juridical_chunks(doc_content, max_len=600)
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=[
                r"\nCAPÍTULO\s",
                r"\nTÍTULO\s",
                r"\nArt\.?\s",
                r"\n§",
                r"\n[IVXLCDM]+ –",
                r"\n[a-z]\)",
                "\n\n",
                "\n",
                ". ",
                " ",
            ],
        )
        return splitter.split_text(doc_content)
