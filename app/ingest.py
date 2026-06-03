"""
ingest.py  –  Load data/*.txt files, chunk, embed, and store in ChromaDB.
Run:  python ingest.py
"""

import os
import re
import pathlib
import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR    = pathlib.Path(__file__).parent / "data"
CHROMA_DIR  = pathlib.Path(__file__).parent / "chroma_db"
COLLECTION  = "meridian_brain"
CHUNK_WORDS = 200  # smaller chunks keep each topic/section in its own embedding


def _chunk_text(text: str, max_words: int = CHUNK_WORDS) -> list[str]:
    """Split text into ~max_words-word chunks.

    Splits first on the section-header lines (===...===) so that each named
    section (e.g. COMMISSION RATES, DISCOUNTS, ROOF NOTES) starts a new chunk.
    Within each section, further splits on double-newlines if the section is
    still larger than max_words.
    """
    # Break on separator lines (== repeated 5+ times)
    sections = re.split(r"\n={5,}\n", text)
    paragraphs: list[str] = []
    for sec in sections:
        # Within each section split further on blank lines
        paras = [p.strip() for p in re.split(r"\n{2,}", sec) if p.strip()]
        paragraphs.extend(paras)

    chunks, current, current_words = [], [], 0
    for para in paragraphs:
        word_count = len(para.split())
        if current_words + word_count > max_words and current:
            chunks.append("\n\n".join(current))
            current, current_words = [], 0
        current.append(para)
        current_words += word_count
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def ingest():
    txt_files = sorted(DATA_DIR.rglob("*.txt"))
    if not txt_files:
        print("No .txt files found under data/")
        return

    model = SentenceTransformer("all-MiniLM-L6-v2")

    client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Wipe and recreate so re-runs don't duplicate chunks
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    total_chunks = 0
    for filepath in txt_files:
        rel        = filepath.relative_to(DATA_DIR)
        category   = rel.parts[0] if len(rel.parts) > 1 else "root"
        source     = str(rel)
        raw_text   = filepath.read_text(encoding="utf-8")
        chunks     = _chunk_text(raw_text)

        ids        = [f"{source}::chunk{i}" for i in range(len(chunks))]
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()
        metadatas  = [{"source": source, "category": category} for _ in chunks]

        collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        print(f"  {source:45s}  {len(chunks)} chunks")
        total_chunks += len(chunks)

    print(f"\nIngested {total_chunks} chunks from {len(txt_files)} files into '{COLLECTION}'.")


if __name__ == "__main__":
    ingest()
