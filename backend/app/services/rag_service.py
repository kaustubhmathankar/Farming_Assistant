from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import settings


@lru_cache(maxsize=1)
def embeddings():
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


@lru_cache(maxsize=1)
def vectorstore():
    Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory,
        embedding_function=embeddings(),
    )


def retrieve(query: str, k: int | None = None) -> list[Document]:
    return vectorstore().similarity_search(query, k=k or settings.rag_top_k)


def format_documents(docs: list[Document]) -> tuple[str, list[dict]]:
    sources = []
    chunks = []
    seen = set()
    for doc in docs:
        meta = doc.metadata or {}
        title = meta.get("title") or meta.get("source") or "Agriculture knowledge"
        key = (title, meta.get("url"))
        if key not in seen:
            sources.append({"title": title, "source": meta.get("organization", "Agriculture knowledge"), "url": meta.get("url"), "type": "knowledge"})
            seen.add(key)
        chunks.append(doc.page_content[:5000])
    return "\n\n---\n\n".join(chunks), sources


def ingest_directory(directory: str | Path) -> int:
    directory = Path(directory)
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.rag_chunk_size, chunk_overlap=settings.rag_chunk_overlap)
    docs = []
    for path in directory.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        docs.extend(splitter.split_documents([Document(page_content=text, metadata={"source": path.name, "title": path.stem})]))
    if docs:
        vectorstore().add_documents(docs)
    return len(docs)
