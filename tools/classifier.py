from pathlib import Path
import re
from typing import Optional, Tuple
import joblib


class IntentClassifier:
    def __init__(
        self,
        model_dir: str | Path = Path(__file__).parent / "model",
        margin_threshold: float = 0.15,
    ):
        model_dir = Path(model_dir)
        self.threshold = margin_threshold
        self.vectorizer = joblib.load(model_dir / "vectorizer.joblib")
        self.clf = joblib.load(model_dir / "classifier.joblib")

    @staticmethod
    def isGreeting(text: str) -> bool:
        normalized = " ".join(re.sub(r"[^a-z\s']", " ", text.lower()).split())
        if normalized in {
            "what's up",
            "whats up",
            "what is up",
            "hey what's up",
            "hey whats up",
            "hey what is up",
        }:
            return True
        return bool(
            re.fullmatch(
                r"(?:hey|hi|hello|hiya|yo|howdy)(?: nova)?(?:\s+(?:there|friend))?",
                normalized,
            )
        )

    @staticmethod
    def isGeneratedFileRequest(text: str) -> bool:
        """Return whether a file request also asks NOVA to generate its text."""
        normalized = text.lower()
        has_file_request = bool(re.search(r"\bfile\b", normalized))
        has_content_action = bool(
            re.search(r"\b(?:write|writing|draft|generate|create|add|put|include)\b", normalized)
        )
        has_text_content = bool(
            re.search(r"\b(?:text|content|paragraph|sentence|writing)\b", normalized)
        )
        return has_file_request and has_content_action and has_text_content

    def predict(self, text: str) -> Tuple[Optional[str], float]:
        if not text or not text.strip():
            return None, 0.0

        if self.isGreeting(text):
            return "LLM", 1.0

        if self.isGeneratedFileRequest(text):
            return "LLM", 1.0

        X = self.vectorizer.transform([text])
        probs = self.clf.predict_proba(X)[0]
        ranked_idx = probs.argsort()[::-1]

        top_idx, second_idx = ranked_idx[0], ranked_idx[1]
        top_conf = float(probs[top_idx])
        margin = top_conf - float(probs[second_idx])

        if margin < self.threshold:
            return None, top_conf

        return str(self.clf.classes_[top_idx]), top_conf