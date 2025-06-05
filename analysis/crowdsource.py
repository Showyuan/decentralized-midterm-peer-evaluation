#!/usr/bin/python

import average_voting
import user_model
import item_model
import graph_builder
import reputation_instrumented
import numpy as np

N_USERS = 50
N_ITEMS = 50
N_REVIEWS = 6
BIAS_STDEV = 0.0
EVAL_STDEV = 0.4
FRACTION_BAD = 0.2
GAMMA_SHAPE = 2
N_ITERATIONS = 10
DO_PLOTS = False

def eval_quality(values):
    diffs = [values[it] - it.q for it in items]
    stdev = np.std(diffs)
    a = [values[it] for it in items]
    b = [it.q for it in items]
    r = np.corrcoef(a, b)[1, 0]
    return stdev, r

# 在使用者和項目之間建立圖。

avs = []
acs = []
rvs = []
rcs = []
for i in range(N_ITERATIONS):
    users = [user_model.User(bias_stdev=BIAS_STDEV, eval_stdev=EVAL_STDEV, mode='gamma', 
                             gamma_shape=GAMMA_SHAPE, frac=FRACTION_BAD)
             for u in range(N_USERS)]
    items = [item_model.Item() for i in range(N_ITEMS)]
    graph = graph_builder.Graph(items, users, reviews=N_REVIEWS)
    # 根據簡單平均評估。
    values_via_avg = average_voting.evaluate_items(graph)
    av, ac = eval_quality(values_via_avg)
    print("  Via average: ", av, ac)
    avs.append(av)
    acs.append(ac)
    # 根據聲譽系統評估。
    values_via_rep = reputation_instrumented.evaluate_items(graph, do_plots=DO_PLOTS)
    rv, rc = eval_quality(values_via_rep)
    print("  Via reputation:", rv, rc)
    rvs.append(rv)
    rcs.append(rc)
print("Stdev via average:", np.average(avs))
print("Stdev via reputation:", np.average(rvs))
print("Correlation via average:", np.average(acs))
print("Correlation via reputation:", np.average(rcs))


