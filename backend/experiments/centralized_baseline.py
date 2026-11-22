from federated.dataset import create_dataset
from federated.model import SimpleLogisticModel


def main():
    xtr, xte, ytr, yte = create_dataset(600, 8, 42)
    model = SimpleLogisticModel(xtr.shape[1]).fit(xtr, ytr, epochs=40, lr=0.05)
    metrics = __import__('federated.model', fromlist=['classification_metrics']).classification_metrics(yte, model.predict(xte))
    print("Centralized baseline:", metrics)


if __name__ == "__main__":
    main()
