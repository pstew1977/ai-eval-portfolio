"""
Build a small Chroma vector store from documents.py.

Uses OpenAI embeddings (via chromadb's built-in OpenAIEmbeddingFunction) so
the whole project - indexing, generation, and Ragas judging - runs off the
one OPENAI_API_KEY you already set up in Week 1. No separate model download
needed.

Run with:
    python build_index.py

This creates a persistent Chroma store in ./chroma_db - re-running this
script will recreate the collection from scratch (safe to run repeatedly).
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from documents import DOCS

load_dotenv()  # picks up OPENAI_API_KEY from ../.env or a local .env


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY not set. Copy ../.env into this folder, or set "
            "the environment variable directly."
        )

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )

    client = chromadb.PersistentClient(path="./chroma_db")

    # Start fresh each time this script runs.
    try:
        client.delete_collection("fabric_kb")
    except Exception:
        pass

    collection = client.create_collection(
        name="fabric_kb",
        embedding_function=embedding_fn,
    )

    collection.add(
        ids=[d["id"] for d in DOCS],
        documents=[d["text"] for d in DOCS],
        metadatas=[{"title": d["title"]} for d in DOCS],
    )

    print(f"Indexed {len(DOCS)} documents into ./chroma_db (collection: fabric_kb)")


if __name__ == "__main__":
    main()
