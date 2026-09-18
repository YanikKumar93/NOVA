"""
agent/pipeline.py — intent classification + optional RAG context prep.
"""

from tools.rag import ask_document


def classifyIntent(message: str) -> str:
    """Return intent label for one user message."""
    msg = (message or "").lower()
    rag_keywords = [
        "ppt",
        "presentation",
        "lecture",
        "pdf",
        "slide",
        "study material",
        "notes",
        "document",
        "chapter",
        "syllabus",
        "explain file",
        "uploaded",
        "what is this ppt",
        "from the file",
        "from the pdf",
    ]
    if any(keyword in msg for keyword in rag_keywords):
        return "study_material_rag"
    return "conversation"


def retrieveContext(message: str, intent: str) -> str:
    """Retrieve extra context for special intents. Never raise."""
    if intent != "study_material_rag":
        return ""
    try:
        return ask_document(message)
    except Exception as error:
        return f"FALLBACK:RAG_ERROR | Could not retrieve document context: {error}"


def prepareMessage(message: str) -> str:
    """Prepare one user message. On any failure, return original message."""
    try:
        intent = classifyIntent(message)
        context = retrieveContext(message, intent)

        if not context:
            return message

        if context.startswith("FALLBACK:"):
            return (
                f"{message}\n\n"
                "Note: document retrieval was unavailable or empty. "
                "Answer helpfully without inventing file contents. "
                f"Details: {context}"
            )

        return (
            f"{message}\n\n"
            "Use the following retrieved document context when relevant:\n"
            f"{context}"
        )
    except Exception:
        return message