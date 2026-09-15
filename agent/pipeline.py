#for future streamlit implementation of intent classifier and rag.


def classifyIntent(message: str) -> str:
    """Return the current fallback intent until a classifier is connected."""
    return "conversation"


def retrieveContext(message: str, intent: str) -> str:
    """Return retrieved context when a future RAG backend is available."""
    return ""


def prepareMessage(message: str) -> str:
    """Prepare one user message without changing current NOVA behavior."""
    intent = classifyIntent(message)
    context = retrieveContext(message, intent)
    if not context:
        return message
    return (
        f"{message}"
        "Use the following retrieved context when it is relevant:\n"
        f"{context}"
    )