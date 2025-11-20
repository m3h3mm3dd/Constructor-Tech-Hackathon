"""
RAG (Retrieval‑Augmented Generation) API routes.

These endpoints expose functionality for ingesting documents into a vector
database and retrieving relevant context for a user query. RAG reduces
hallucinations by grounding LLM responses in factual data. According to
DataCamp’s tutorial, RAG works by first retrieving relevant information
from external sources and then feeding it into the language model【438448550825859†L103-L139】. Key
components include document loaders, text splitting, indexing, vector
stores, retrievers, and generative models【438448550825859†L150-L172】. This router
implements ingestion and retrieval; the generation step is handled in
``chat_service.py``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...core.security import get_api_key
from ...services.rag_service import ingest_documents, retrieve_context


router = APIRouter()


class IngestRequest(BaseModel):
    texts: list[str] = Field(..., description="List of raw text documents to ingest.")
    metadata: list[dict] | None = Field(None, description="Optional metadata for each document.")


class IngestResponse(BaseModel):
    ingested: int = Field(..., description="Number of documents ingested after splitting into chunks.")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(
    request: IngestRequest,
    api_key: str = Depends(get_api_key),
) -> IngestResponse:
    """Ingest raw documents into the vector store.

    This endpoint splits each text into chunks, embeds them with OpenAI's
    embeddings API, and stores them in a vector DB. It returns the number
    of chunks ingested. If metadata is provided, it is stored alongside
    each chunk.
    """
    await ingest_documents(request.texts, request.metadata)
    # Approximate ingested chunk count as sum of splits (not exact but provides feedback)
    chunk_count = 0
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    for text in request.texts:
        chunk_count += len(splitter.split_text(text))
    return IngestResponse(ingested=chunk_count)


class RetrieveRequest(BaseModel):
    query: str = Field(..., description="The search query to retrieve relevant chunks.")
    k: int = Field(4, description="Number of chunks to retrieve.")


class RetrieveChunk(BaseModel):
    text: str
    score: float


class RetrieveResponse(BaseModel):
    results: list[RetrieveChunk]


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_endpoint(
    request: RetrieveRequest,
    api_key: str = Depends(get_api_key),
) -> RetrieveResponse:
    """Retrieve relevant document chunks for a query.

    This endpoint converts the query into a vector, performs a similarity
    search in the vector database, and returns the top-k chunks with their
    similarity scores.
    """
    results = await retrieve_context(request.query, k=request.k)
    return RetrieveResponse(results=[RetrieveChunk(text=t, score=s) for t, s in results])