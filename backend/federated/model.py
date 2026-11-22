import numpy as np


class SimpleLogisticModel:
    def __init__(self, n_features):
        self.weights = np.zeros(n_features, dtype=float)
        self.bias = np.zeros(1, dtype=float)

    def get_parameters(self):
        return {"weights": self.weights.copy(), "bias": self.bias.copy()}

    def set_parameters(self, state):
        self.weights = np.asarray(state["weights"], dtype=float).copy()
        self.bias = np.asarray(state["bias"], dtype=float).copy()

    def predict_proba(self, x):
        z = np.clip(x @ self.weights + self.bias[0], -50, 50)
        return 1.0 / (1.0 + np.exp(-z))

    def predict(self, x):
        return (self.predict_proba(x) >= 0.5).astype(int)

    def fit(self, x, y, epochs=10, lr=0.05):
        y = y.astype(float)
        for _ in range(epochs):
            p = self.predict_proba(x)
            error = p - y
            self.weights -= lr * (x.T @ error) / len(x)
            self.bias[0] -= lr * np.mean(error)
        return self


def classification_metrics(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    accuracy = (tp + tn) / len(y_true) if len(y_true) else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1,
            "tp": tp, "tn": tn, "fp": fp, "fn": fn}
