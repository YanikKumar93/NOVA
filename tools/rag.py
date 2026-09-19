"""
tools/rag.py — RAG document teaching tool for NOVA.

Supports PDF, PPTX, TXT/MD.
Uses local ChromaDB + sentence-transformers embeddings.
Lazy-loads heavy deps so Streamlit startup stays fast.
"""

import os
import socket

socket.setdefaulttimeout(120.0)

CHROMA_DATA_PATH = os.environ.get("NOVA_CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "nova_documents"
_ACTIVE_DOC_PATH = os.path.join(CHROMA_DATA_PATH, "_active_doc.txt")

_client = None
_collection = None


def set_active_document(filename: str) -> None:
    """Mark this filename as the currently active document for ask_document()."""
    os.makedirs(CHROMA_DATA_PATH, exist_ok=True)
    with open(_ACTIVE_DOC_PATH, "w", encoding="utf-8") as f:
        f.write(filename)


def get_active_document() -> str:
    """Return the filename of the currently active document, or '' if none."""
    try:
        with open(_ACTIVE_DOC_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def _get_collection():
    """Lazy init Chroma collection; auto-heal embedding conflicts."""
    global _client, _collection
    if _collection is not None:
        return _collection

    import chromadb
    from chromadb.utils import embedding_functions

    _client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

    try:
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    except Exception:
        embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    try:
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )
    except ValueError:
        # Old DB used a different embedding function — reset collection once.
        try:
            _client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )

    return _collection


def _extract_text(file_path: str) -> str:
    """Extract raw text from PDF, PPTX, or TXT/MD."""
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pptx":
            from pptx import Presentation

            prs = Presentation(file_path)
            slides_text = []
            for i, slide in enumerate(prs.slides, start=1):
                slide_content = [f"--- Slide {i} ---"]
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slide_content.append(shape.text.strip())
                slides_text.append("\n".join(slide_content))
            return "\n\n".join(slides_text).strip()

        if ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            pages_text = []
            for i, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                pages_text.append(f"--- Page {i} ---\n{page_text.strip()}")
            return "\n\n".join(pages_text).strip()

        if ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()

        return f"Unsupported file type '{ext}'. Supported: .pptx, .pdf, .txt, .md"

    except Exception as error:
        return f"Error reading file '{file_path}': {error}"


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)
    step = max(1, chunk_size - overlap)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start += step

    return chunks


def ingest_document(file_path: str, semester: str = "", subject: str = "") -> str:
    """Read a document, chunk it, embed it, and store it in ChromaDB.

    Args:
        file_path: Local path to the uploaded document file.
        semester: Optional semester tag (e.g. '3').
        subject: Optional subject tag (e.g. 'Theory of Computation').
    """
    if not file_path or not str(file_path).strip():
        return "File path cannot be empty."

    if not os.path.exists(file_path):
        return f"File does not exist: {file_path}"

    filename = os.path.basename(file_path)
    text = _extract_text(file_path)

    if not text:
        return f"No extractable text found in '{filename}'."
    if text.startswith("Unsupported") or text.startswith("Error"):
        return text

    chunks = _chunk_text(text)
    if not chunks:
        return f"Could not create text chunks from '{filename}'."

    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "filename": filename,
            "semester": str(semester or "").strip(),
            "subject": str(subject or "").strip(),
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    try:
        collection = _get_collection()
        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        set_active_document(filename)
        return (
            f"Successfully processed '{filename}' into {len(chunks)} chunks "
            "in vector store."
        )
    except Exception as error:
        return f"Failed to store embeddings for '{filename}': {error}"

def ask_document(question: str) -> str:
    """Search uploaded study materials and return relevant context.

    Args:
        question: The user's query about the uploaded document.
    """
    if not question or not str(question).strip():
        return "Please ask a specific question about the document."

    active_file = get_active_document()
    if not active_file:
        return (
            "FALLBACK:NO_DOCS | No documents have been uploaded yet. "
            "Please upload a PPTX/PDF/TXT file first from the sidebar."
        )

    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return (
                "FALLBACK:NO_DOCS | No documents have been uploaded yet. "
                "Please upload a PPTX/PDF/TXT file first from the sidebar."
            )

        results = collection.query(
            query_texts=[question],
            n_results=3,
            where={"filename": active_file},
        )
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]

        if not docs:
            return (
                "FALLBACK:EMPTY_RETRIEVAL | I searched the uploaded material "
                "but found nothing clearly relevant. Try rephrasing."
            )

        pieces = []
        for doc, meta in zip(docs, metas or [{}] * len(docs)):
            src = (meta or {}).get("filename", "Document")
            pieces.append(f"[{src}]: {doc}")

        return "Retrieved Context from Uploaded Files:\n" + "\n\n".join(pieces)

    except Exception as error:
        return (
            "FALLBACK:RAG_ERROR | Document search failed "
            f"({type(error).__name__}: {error}). "
            "I can still answer generally without the file."
        )