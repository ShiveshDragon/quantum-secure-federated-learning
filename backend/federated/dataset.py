import os
import numpy as np
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT_HOSPITAL_DATA_PATH = os.path.join(DATA_DIR, "hospital_data.csv")


def load_csv_dataset(
    csv_path: Optional[str] = None, 
    target_col: str = "target", 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """Load clinical hospital dataset from CSV, scale features, and split into train/test sets.
    
    Args:
        csv_path: Path to CSV file. Defaults to backend/data/hospital_data.csv.
        target_col: Name of binary ground-truth column (0 = healthy, 1 = risk).
        test_size: Proportion of dataset to include in test split.
        random_state: Random state for reproducible train/test split.
        
    Returns:
        (x_train_scaled, x_test_scaled, y_train, y_test, feature_names)
    """
    path = csv_path or DEFAULT_HOSPITAL_DATA_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found at: {path}")

    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    target_clean = target_col.strip().lower()

    if target_clean not in df.columns:
        # Fallback: check if 'target' or 'label' or 'outcome' exists
        candidates = [c for c in df.columns if c in ("target", "label", "outcome", "diagnosis", "class")]
        if candidates:
            target_clean = candidates[0]
        else:
            raise ValueError(f"Target column '{target_col}' not found in CSV. Available columns: {list(df.columns)}")

    feature_cols = [c for c in df.columns if c != target_clean]
    if len(feature_cols) == 0:
        raise ValueError("CSV contains no feature columns other than target.")

    # Convert all feature columns to numeric, filling NaNs with column median
    X_df = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    X_df = X_df.fillna(X_df.median())
    X = X_df.values.astype(np.float64)

    y = pd.to_numeric(df[target_clean], errors="coerce").fillna(0).values.astype(int)
    # Ensure binary 0 or 1
    y = np.where(y > 0, 1, 0)

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    scaler = StandardScaler().fit(x_train)
    return scaler.transform(x_train), scaler.transform(x_test), y_train, y_test, feature_cols


def get_dataset_summary(csv_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve statistical summary and preview of the hospital CSV dataset."""
    path = csv_path or DEFAULT_HOSPITAL_DATA_PATH
    if not os.path.exists(path):
        return {
            "exists": False,
            "path": path,
            "message": "No CSV file uploaded yet."
        }

    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    target_col = "target" if "target" in df.columns else df.columns[-1]
    feature_cols = [c for c in df.columns if c != target_col]
    
    y = pd.to_numeric(df[target_col], errors="coerce").fillna(0).values.astype(int)
    y_binary = np.where(y > 0, 1, 0)
    pos_count = int(np.sum(y_binary == 1))
    neg_count = int(np.sum(y_binary == 0))

    return {
        "exists": True,
        "path": path,
        "filename": os.path.basename(path),
        "total_rows": int(len(df)),
        "n_features": len(feature_cols),
        "feature_names": feature_cols,
        "target_col": target_col,
        "positive_cases": pos_count,
        "negative_cases": neg_count,
        "positive_ratio": round(pos_count / max(1, len(df)), 3),
        "sample_preview": df.head(5).to_dict(orient="records")
    }


def create_dataset(
    n_samples: int = 600, 
    n_features: int = 8, 
    random_state: int = 42, 
    source: str = "synthetic", 
    csv_path: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create or load dataset for Federated Learning.
    
    Args:
        n_samples: Number of samples if generating synthetic data.
        n_features: Number of features if generating synthetic data.
        random_state: Random seed for reproducibility.
        source: 'synthetic' (default) or 'hospital'/'csv'.
        csv_path: Optional custom CSV file path.
        
    Returns:
        (x_train, x_test, y_train, y_test)
    """
    if source in ("csv", "hospital") or csv_path is not None:
        path = csv_path or DEFAULT_HOSPITAL_DATA_PATH
        if os.path.exists(path):
            x_tr, x_te, y_tr, y_te, _ = load_csv_dataset(path, random_state=random_state)
            return x_tr, x_te, y_tr, y_te

    # Default synthetic classification dataset (preserves exact test suite behavior)
    x, y = make_classification(
        n_samples=n_samples, n_features=n_features,
        n_informative=max(2, n_features // 2), n_redundant=min(1, n_features - 2),
        n_clusters_per_class=1, class_sep=1.2, random_state=random_state
    )
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=random_state, stratify=y
    )
    scaler = StandardScaler().fit(x_train)
    return scaler.transform(x_train), scaler.transform(x_test), y_train, y_test


def split_clients(x: np.ndarray, y: np.ndarray, n_clients: int = 5, non_iid: bool = False):
    """Partition dataset across IoT client nodes (IID uniform or Non-IID label skew)."""
    if n_clients not in (4, 5):
        raise ValueError("project configuration expects 4 or 5 clients")
    if len(x) < n_clients:
        raise ValueError("not enough samples")
    if not non_iid:
        indices = np.array_split(np.arange(len(x)), n_clients)
    else:
        # Simple deterministic label-skew split: sort by label then shard.
        ordered = np.argsort(y)
        indices = np.array_split(ordered, n_clients)
    return [(f"client{i+1}", x[idx], y[idx]) for i, idx in enumerate(indices)]

