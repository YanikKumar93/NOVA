"""Minimal routing logs for checking classifier behavior."""

import json
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path("logs/routing.jsonl")


def logRoutingDecision(
    classifierIntent: str | None,
    confidence: float,
    route: str,
    tool: str | None = None,
    reason: str | None = None,
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classifier_intent": classifierIntent,
        "confidence": confidence,
        "route": route,
        "tool": tool,
        "reason": reason,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as logFile:
            logFile.write(json.dumps(record) + "\n")
    except OSError:
        # Logging must never prevent NOVA from answering.
        pass