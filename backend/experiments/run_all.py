"""Run the reproducible technical experiment suite (requires dependencies)."""
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from experiments.centralized_baseline import main as centralized
from experiments.federated_baseline import main as federated
from experiments.secure_fl_demo import main as secure
from experiments.eavesdropping import main as eve
from experiments.noise_experiment import main as noise
from experiments.security_comparison import main as security
from experiments.performance import main as performance
from experiments.compare_models import main as compare
from experiments.robust_aggregation_experiment import main as robust_agg


def main():
    for name, fn in [("centralized",centralized),("federated",federated),("secure",secure),
                     ("eavesdropping",eve),("noise",noise),("security",security),
                     ("performance",performance),("comparison",compare),
                     ("robust_aggregation", robust_agg)]:
        print(f"\n=== {name.upper()} ===")
        fn()

if __name__ == "__main__": main()
