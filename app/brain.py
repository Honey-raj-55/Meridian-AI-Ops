"""
brain.py  –  Query the Meridian knowledge base via ChromaDB + Gemini 1.5 Flash.
Usage:
    from brain import query_brain
    result = query_brain("What is Safeco's commission rate for new business?")
    print(result["answer"])

    # or run directly:
    python brain.py "What roof age does Safeco refuse to write?"
"""

import os
import sys
import pathlib
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# Pull keys from Streamlit secrets when running on Streamlit Cloud
try:
    import streamlit as st
    for _k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "USE_LLM"):
        if _k in st.secrets and not os.getenv(_k):
            os.environ[_k] = st.secrets[_k]
except Exception:
    pass

CHROMA_DIR  = pathlib.Path(__file__).parent / "chroma_db"
COLLECTION  = "meridian_brain"
TOP_K       = 6

_model      = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client      = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(COLLECTION)
    return _collection


SYSTEM_PROMPT = """\
You are Meridian, an internal knowledge assistant for C1 Insurance Group and MyUtilities.
You answer questions strictly from the context passages provided below.

Rules you must follow without exception:
1. Base every answer only on the provided context. Do not recall or invent any rates,
   coverage limits, commissions, provider details, or procedures from your general training.
2. If the context does not contain enough information to answer the question, say exactly:
   "I don't have enough information in the knowledge base to answer that confidently."
3. Never fabricate specific numbers (premiums, percentages, deductibles, commission rates).
   If a number is in the context, you may state it. If it is not, do not estimate.
4. Be concise and direct. Use bullet points when listing multiple items.
5. When you cite a specific fact, note the source document in parentheses,
   e.g. (carriers/safeco.txt).

Context:
{context}
"""


def query_brain(question: str) -> dict:
    """
    Embed question, retrieve top-K context chunks, ask Gemini, return result.

    Returns:
        {
            "answer":  str,
            "sources": list[str],   # deduplicated source filenames
            "chunks":  list[str],   # raw retrieved passages (for debugging)
        }
    """
    embedding  = _get_model().encode([question]).tolist()[0]
    collection = _get_collection()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    sources   = list(dict.fromkeys(m["source"] for m in metadatas))  # ordered dedup

    context_text = "\n\n---\n\n".join(
        f"[Source: {metadatas[i]['source']}]\n{documents[i]}"
        for i in range(len(documents))
    )

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found.")
        genai.configure(api_key=api_key)
        gemini   = genai.GenerativeModel("gemini-2.5-flash")
        prompt   = SYSTEM_PROMPT.format(context=context_text) + f"\n\nQuestion: {question}"
        response = gemini.generate_content(prompt)
        answer   = response.text.strip()
    except Exception:
        answer = _fallback_answer(documents, metadatas)

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  documents,
    }


def _fallback_answer(documents: list[str], metadatas: list[dict]) -> str:
    """Build a readable answer directly from retrieved chunks when Gemini is unavailable."""
    header = (
        "Demo fallback: Gemini quota/API unavailable, "
        "answering from retrieved knowledge base context.\n"
    )
    bullets = []
    for doc, meta in zip(documents, metadatas):
        source = meta.get("source", "unknown")
        for raw_line in doc.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("=") or line.startswith("-" * 10):
                continue
            # Keep lines that look substantive (contain a colon, a number, or start with -)
            if ":" in line or any(c.isdigit() for c in line) or line.startswith("-"):
                bullets.append(f"- {line.lstrip('- ')} ({source})")
                if len(bullets) >= 12:
                    break
        if len(bullets) >= 12:
            break

    body = "\n".join(bullets) if bullets else "- No specific details found in retrieved context."
    return f"{header}\n{body}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python brain.py \"your question here\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"\nQuestion: {question}\n")

    result = query_brain(question)

    print("Answer:")
    print(result["answer"])
    print("\nSources used:")
    for s in result["sources"]:
        print(f"  - {s}")
