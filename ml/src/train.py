"""Train a classifier on windowed data and save model + metadata.

Model type is configurable (random_forest / logistic_regression / svm), so this
same code trains on any labelled dataset. Metadata (feature order, class names,
window params, scaler) is saved alongside the model for consistent inference.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .config import PipelineConfig


@dataclass
class TrainResult:
    model_path: str
    accuracy: float
    report: str
    confusion: np.ndarray
    class_names: List[str]
    feature_cols: List[str]
    n_samples: int
    n_features: int
    extra: Dict = field(default_factory=dict)


def build_model(cfg: PipelineConfig) -> Pipeline:
    """Construct the estimator (with StandardScaler) using per-type params."""
    mtype = cfg.model_type.lower()

    # Start from that model type's defaults, then apply any user overrides.
    params = dict(cfg.default_params.get(mtype, {}))
    params.update(cfg.model_params)

    if mtype == "random_forest":
        est = RandomForestClassifier(**params)
        # Scaler is harmless for RF; keep pipeline uniform across model types.
        return Pipeline([("scaler", StandardScaler()), ("clf", est)])
    if mtype == "logistic_regression":
        params.setdefault("max_iter", 2000)
        est = LogisticRegression(**params)
        return Pipeline([("scaler", StandardScaler()), ("clf", est)])
    if mtype == "svm":
        params.setdefault("probability", True)
        est = SVC(**params)
        return Pipeline([("scaler", StandardScaler()), ("clf", est)])

    raise ValueError(
        f"Unknown model_type '{cfg.model_type}'. "
        "Use: random_forest, logistic_regression, svm"
    )


def train(
    X: np.ndarray,
    y: np.ndarray,
    class_names: List[str],
    feature_cols: List[str],
    cfg: PipelineConfig,
) -> TrainResult:
    """Split, train, evaluate, and persist the model + metadata."""
    # Stratify only if every class has >=2 samples (required by the splitter).
    counts = np.bincount(y, minlength=len(class_names))
    can_stratify = counts.min() >= 2 and len(class_names) > 1

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        stratify=y if can_stratify else None,
    )

    model = build_model(cfg)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    report = classification_report(
        y_test, y_pred, target_names=class_names, zero_division=0
    )
    conf = confusion_matrix(y_test, y_pred, labels=list(range(len(class_names))))

    os.makedirs(cfg.output_dir, exist_ok=True)
    model_path = os.path.join(cfg.output_dir, f"{cfg.model_name}.joblib")

    payload = {
        "model": model,
        "class_names": class_names,
        "feature_cols": feature_cols,
        "window_size": cfg.window_size,
        "window_stride": cfg.window_stride,
        "model_type": cfg.model_type,
    }
    joblib.dump(payload, model_path)

    return TrainResult(
        model_path=model_path,
        accuracy=acc,
        report=report,
        confusion=conf,
        class_names=class_names,
        feature_cols=feature_cols,
        n_samples=int(X.shape[0]),
        n_features=int(X.shape[1]),
    )

