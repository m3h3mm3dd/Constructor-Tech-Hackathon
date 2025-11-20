"""
Retrieval‑Augmented Generation (RAG) service.

This module provides helper functions to ingest documents into a vector
database and retrieve relevant context for user queries. It uses the
``langchain`` library with an in-memory Chroma vector store by default,
but can be configured to connect to external vector databases via
environment variables. See the configuration in ``config.py`` for
customization options.

The high‑level process for a RAG system is:

1. Load and split documents into manageable chunks (document loaders,
   text splitters).
2. Embed each chunk into a vector space using an embedding model.
3. Store the embeddings in a vector database for efficient similarity
   search.
4. On user query, convert the question into a vector, perform a search
   against the vector database to retrieve the most relevant chunks,
   and combine them with the question in a prompt to the language model.

For reference on the RAG workflow, see DataCamp's guide which explains
that RAG combines retrieving real information from datasets with LLMs to
produce accurate, relevant responses【438448550825859†L103-L139】. Key components
include document loaders, text splitting, indexing (vector stores),
retrievers, and generative models【438448550825859†L150-L172】.

This service abstracts the ingestion and retrieval steps. The actual
generation step should be handled in ``chat_service.py`` or another
module by combining the retrieved context with the user's question
before calling the language model.
"""

from __future__ import annotations

import asyncio
from typing import Iterable, List, Tuple

try:
    from langchain.docstore.document import Document  # type: ignore
    from langchain.embeddings import OpenAIEmbeddings  # type: ignore
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
    from langchain.vectorstores import Chroma  # type: ignore
except Exception as e:  # pragma: no cover
    # If langchain isn't installed, raise a clear error when functions are used
    Document = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore
    RecursiveCharacterTextSplitter = None  # type: ignore
    Chroma = None  # type: ignore

from ..core.config import settings


# Create a global vector store. For production, consider initializing
# this in a startup event and storing the instance on the app state.
_vector_store: Chroma | None = None


def get_vector_store() -> Chroma:
    """Get or create a Chroma vector store.

    Returns:
        Chroma: Vector store instance connected to a persistent directory
        (if VECTOR_DB_URL is provided) or in-memory if not.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store
    # Determine persistence directory. If VECTOR_DB_URL is provided, use it.
    persist_dir = None
    if settings.VECTOR_DB_URL:
        persist_dir = settings.VECTOR_DB_URL
    if OpenAIEmbeddings is None or Chroma is None:
        raise ImportError(
            "langchain is not installed. Please install langchain to use the RAG service."
        )
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    _vector_store = Chroma(
        collection_name=settings.VECTOR_COLLECTION,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    return _vector_store


async def ingest_documents(texts: Iterable[str], metadata: Iterable[dict] | None = None) -> None:
    """Ingest a collection of documents into the vector store.

    Args:
        texts (Iterable[str]): Raw text documents.
        metadata (Iterable[dict] | None): Optional metadata for each document.
    """
    # Defer import checks until the function is called
    if OpenAIEmbeddings is None or Document is None or RecursiveCharacterTextSplitter is None:
        raise ImportError(
            "langchain is not installed. Please install langchain to use the RAG service."
        )
    vector_store = get_vector_store()
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    docs: List[Document] = []
    for i, text in enumerate(texts):
        chunks = splitter.split_text(text)
        for chunk in chunks:
            meta = {"source_index": i}
            if metadata and len(metadata) > i:
                meta.update(metadata[i])
            docs.append(Document(page_content=chunk, metadata=meta))
    # Embedding and adding to the vector store can be CPU‑bound; run in a thread
    def _add_docs():
        vector_store.add_documents(docs)  # type: ignore[arg-type]

    await asyncio.to_thread(_add_docs)


async def retrieve_context(query: str, k: int = 4) -> List[Tuple[str, float]]:
    """Retrieve the top‑k most relevant chunks for a given query.

    Args:
        query (str): The user's query.
        k (int): Number of chunks to retrieve.

    Returns:
        List[Tuple[str, float]]: A list of tuples containing chunk text and
            similarity score.
    """
    if OpenAIEmbeddings is None or Document is None:
        raise ImportError(
            "langchain is not installed. Please install langchain to use the RAG service."
        )
    vector_store = get_vector_store()
    # Search can be blocking; run in a thread
    def _search() -> List[Tuple[Document, float]]:
        return vector_store.similarity_search_with_score(query, k=k)
    results = await asyncio.to_thread(_search)
    return [(doc.page_content, score) for doc, score in results]