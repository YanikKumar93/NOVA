#decided to implement a log file to see what classifier is doing.
"""
Json format is {
  "timestamp": "DD/MM HH:MM:SS +05:30",
  "intent": what tool is to be called,
  "message": the actual message user passed,
  "confidence": self explanatory, but it uses margin instead of strict confidence level,
  "route": whether it used system or agent,
  "tool": the tool called,
  "reason": fallback or failure reason
}
"""


import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


LOG_PATH = Path("logs/routing.jsonl")


def _gmt530_timestamp() -> str:
    utc_now = datetime.now(timezone.utc)
    ist = utc_now + timedelta(hours=5, minutes=30)
    return ist.strftime("%d/%m %H:%M:%S +05:30")


def logRouteDecision(
    message: str,
    classifierIntent: str | None,
    confidence: float,
    route: str,
    medium: str = "app",
    tool: str | None = None,
    parsedArguments: list | None = None,
    toolError: str | None = None,
    reason: str | None = None,
    agentToolCalls: list | None = None,
    fallbackTriggered: bool = False,
    latencyMs: int | None = None,
) -> None:
    record = {
        "timestamp": _gmt530_timestamp(),
        "medium": medium,
        "message": message,
        "classifier_intent": classifierIntent,
        "confidence": confidence,
        "route": route,
        "tool": tool,
        "parsed_arguments": parsedArguments,
        "tool_error": toolError,
        "reason": reason,
        "agent_tool_calls": agentToolCalls or [],
        "fallback_triggered": fallbackTriggered,
        "latency_ms": latencyMs,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as logFile:
            logFile.write(json.dumps(record) + "\n")
    except OSError:
        pass


def latestRouteDecision() -> dict:
    #bc ye chal kyu nhi rha streamlit me
    try:
        if not LOG_PATH.exists():
            return {}
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1]) if lines else {}
    except (OSError, json.JSONDecodeError):
        return {}