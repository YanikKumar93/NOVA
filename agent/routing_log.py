#decided to implement a log file to see what classifier is doing.
"""
Json format is {
  "classifier_intent": what tool is to be called,
  "confidence": self explanatory, but it uses margin instead of strict confidence level,
  "route": whether it used system or agent
  "tool": the tool called
}
"""


import json
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path("logs/routing.jsonl")


def logRouteDecision(
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
          pass


def latestRouteDecision() -> dict:
    """Return the most recent routing decision for the Streamlit status panel."""
    try:
        if not LOG_PATH.exists():
            return {}
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1]) if lines else {}
    except (OSError, json.JSONDecodeError):
        return {}