import numpy as np
from federated.fedavg import fedavg, fedavg_state_dict

def test_manual_weighted_average(): assert np.allclose(fedavg([np.array([10.]),np.array([20.])],[1,3]),[17.5])

def test_state_dict_average():
    s=[{"weights":np.array([1.,2.]),"bias":np.array([1.])},{"weights":np.array([3.,4.]),"bias":np.array([3.])}]
    r=fedavg_state_dict(s,[1,1]); assert np.allclose(r["weights"],[2,3]); assert np.allclose(r["bias"],[2])
