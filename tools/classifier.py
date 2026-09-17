from pathlib import Path
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

    def predict(self, text: str) -> Tuple[Optional[str], float]:
        X = self.vectorizer.transform([text])
        probs = self.clf.predict_proba(X)[0]
        ranked_idx = probs.argsort()[::-1]

        top_idx, second_idx = ranked_idx[0], ranked_idx[1]
        top_conf = float(probs[top_idx])
        margin = top_conf - float(probs[second_idx])

        if margin < self.threshold:
            return None, top_conf

        return str(self.clf.classes_[top_idx]), top_conf