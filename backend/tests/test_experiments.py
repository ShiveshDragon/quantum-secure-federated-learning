from experiments.common import run_fl

def test_non_iid_pipeline_runs():
    rows,_=run_fl(n_clients=5,rounds=2,secure=False,non_iid=True,seed=13)
    assert len(rows)==2
    assert all(0<=r["f1"]<=1 for r in rows)
