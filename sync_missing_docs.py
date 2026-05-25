#!/usr/bin/env python
"""
sync_missing_docs.py

Script to import .md files from documents/processed/ that are missing from the SQLite DB.
Converts filename format YYYY_NNNN → NNNN_YYYY to match DB title convention.
Also updates the FAISS index incrementally with new documents.

Usage: python sync_missing_docs.py [--dry-run] [--rebuild-faiss]
"""
import os
import sys
import re
import django

# Bootstrap Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'myapi'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapi.settings')
django.setup()

from documents.models import Document
from documents.helpers.chunk_strategy import get_chunks
from documents.helpers.normalize import normalize
from langchain.schema import Document as LCDocument
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), 'documents', 'processed')
FAISS_INDEX_PATH = 'faiss_index'

def filename_to_db_title(filename_stem):
    """Convert YYYY_NNNN → NNNN_YYYY (the DB convention)."""
    # Match patterns like 1954_0000, 1961_0079_A, 1964_0241_B, etc.
    m = re.match(r'^(\d{4})_(.+)$', filename_stem)
    if m:
        year = m.group(1)
        rest = m.group(2)
        return f"{rest}_{year}"
    return filename_stem  # fallback: unchanged

def db_title_to_filename_stem(db_title):
    """Convert NNNN_YYYY → YYYY_NNNN (reverse)."""
    # Match NNNN_YYYY or NNNN_SUFFIX_YYYY patterns
    # e.g. 0079_1961 → 1961_0079, 0079_A_1961 → 1961_0079_A
    m = re.match(r'^(.+)_(\d{4})$', db_title)
    if m:
        rest = m.group(1)
        year = m.group(2)
        return f"{year}_{rest}"
    return db_title

def main():
    dry_run = '--dry-run' in sys.argv
    rebuild_faiss = '--rebuild-faiss' in sys.argv

    print("=" * 60)
    print("UERJ ChatBot - Missing Documents Sync")
    print("=" * 60)

    # --- Step 1: Find all .md files in processed/ ---
    all_files = {}  # stem → full path
    for fname in os.listdir(PROCESSED_DIR):
        if fname.endswith('.md'):
            stem = fname[:-3]
            all_files[stem] = os.path.join(PROCESSED_DIR, fname)

    print(f"\nTotal .md files in processed/: {len(all_files)}")

    # --- Step 2: Get existing DB titles and convert to filename convention ---
    existing_titles = set(Document.objects.values_list('title', flat=True))
    print(f"Total documents in DB: {len(existing_titles)}")

    # Build a set of filename stems that already exist in DB
    existing_stems = set()
    for title in existing_titles:
        existing_stems.add(db_title_to_filename_stem(title))

    # --- Step 3: Find missing files ---
    missing = {}
    for stem, path in all_files.items():
        if stem not in existing_stems:
            missing[stem] = path

    print(f"\nMissing files (to import): {len(missing)}")
    if not missing:
        print("Nothing to import. DB is in sync with filesystem.")
        return

    for stem in sorted(missing.keys())[:10]:
        print(f"  - {stem}")
    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more")

    if dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # --- Step 4: Import missing docs to DB ---
    print("\nImporting missing documents into DB...")
    imported = []
    skipped_empty = []

    for stem, path in sorted(missing.items()):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            skipped_empty.append(stem)
            print(f"  SKIP (empty): {stem}")
            continue

        db_title = filename_to_db_title(stem)
        doc = Document.objects.create(title=db_title, content=content)
        imported.append(doc)
        print(f"  ADDED: {stem} -> {db_title} ({len(content)} chars)")

    print(f"\nImported: {len(imported)} documents")
    print(f"Skipped (empty content): {len(skipped_empty)}")

    # --- Step 5: Update FAISS index with new documents ---
    if not imported:
        print("No new documents imported; FAISS update skipped.")
        return

    print("\nUpdating FAISS index with new documents...")
    embeddings = HuggingFaceEmbeddings(model_name=settings.DEFAULT_MODEL)

    # Load existing FAISS index
    if os.path.exists(os.path.join(FAISS_INDEX_PATH, 'index.faiss')) and not rebuild_faiss:
        print("  Loading existing FAISS index...")
        db_faiss = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

        # Build LangChain Documents for new docs only
        new_lc_docs = []
        for doc in imported:
            chunks = get_chunks(doc.content)
            for i, chunk in enumerate(chunks):
                new_lc_docs.append(LCDocument(
                    page_content=normalize(chunk),
                    metadata={
                        'title': doc.title,
                        'id': str(doc.public_id),
                        'chunk_id': i,
                        'text_chunk': chunk,
                    }
                ))
        print(f"  Adding {len(new_lc_docs)} chunks from {len(imported)} new docs...")
        db_faiss.add_documents(new_lc_docs)
        db_faiss.save_local(FAISS_INDEX_PATH)
        print("  FAISS index updated and saved.")
    else:
        # Full rebuild (either no index or --rebuild-faiss flag)
        print("  Building full FAISS index from all DB documents...")
        all_docs = Document.objects.exclude(content__isnull=True).exclude(content__exact='')
        lc_docs = []
        for doc in all_docs:
            chunks = get_chunks(doc.content)
            for i, chunk in enumerate(chunks):
                lc_docs.append(LCDocument(
                    page_content=normalize(chunk),
                    metadata={
                        'title': doc.title,
                        'id': str(doc.public_id),
                        'chunk_id': i,
                        'text_chunk': chunk,
                    }
                ))
        print(f"  Building index with {len(lc_docs)} total chunks...")
        db_faiss = FAISS.from_documents(lc_docs, embeddings)
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        db_faiss.save_local(FAISS_INDEX_PATH)
        print("  Full FAISS index built and saved.")

    print("\n" + "=" * 60)
    print(f"Sync complete! {len(imported)} new documents added.")
    print("=" * 60)

if __name__ == '__main__':
    main()
