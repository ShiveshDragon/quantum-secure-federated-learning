from experiments.common import run_fl, save_json
from federated.dataset import create_dataset
from federated.model import SimpleLogisticModel, classification_metrics


def main():
    xtr,xte,ytr,yte=create_dataset(600,8,42)
    model=SimpleLogisticModel(xtr.shape[1]).fit(xtr,ytr,epochs=40,lr=0.05)
    centralized=classification_metrics(yte,model.predict(xte))
    fl,_=run_fl(5,5,False,seed=42)
    secure,key=run_fl(5,5,True,seed=42)
    result={"centralized":centralized,"federated_final":fl[-1],"secure_federated_final":secure[-1],"qkd":key}
    save_json("model_comparison.json",result)
    print(result)


if __name__ == "__main__": main()
