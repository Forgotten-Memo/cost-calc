
import numpy as np
from typing import List

def expected_frac(p=0.20):
    """
    Calculates effective expectation frac after accounting for pity.
    """
    remaining = 1.0
    expected_value = 0.0

    for i in range(1, 7):
        pi = p * remaining
        expected_value += pi * i
        remaining -= pi

    expected_value += remaining * 7

    return 1 / expected_value

def cumulative_prob(probs: list):
    """
    Calculates the cumulative expected steps
    """
    remaining = 1.0
    expected_value = 0.0

    for i, p in enumerate(probs[:-1]):
        pi = p * remaining
        expected_value += pi * (i+1)
        remaining -= pi
    expected_value += remaining * len(probs)
    return 1 / expected_value

def gen_matrix(probs: list[float], apply_expected_frac: bool = True):
    """
    Generates probability matrix given a list of raw probabilities
    """
    if apply_expected_frac:
        probs = [expected_frac(p) for p in probs]
    chain_length = len(probs)

    P = np.zeros((chain_length+1, chain_length+1))
    for i in range(chain_length):
        P[i][0] = 1 - probs[i]
        P[i][i+1] = probs[i]

    P[chain_length][chain_length] = 1 # absorbing state
    return P

def calc_cost(raw_probs: List[float], cost: List[float | int]):
    """
    Calculates cost given a set of raw probabilities and costs.
    """
    P = gen_matrix(raw_probs)

    absorbing = [i for i in range(len(P)) if P[i][i] == 1 and all(P[i][j] == 0 for j in range(len(P)) if j != i)]
    transient = [i for i in range(len(P)) if i not in absorbing]

    # Compute M = (I - Q)^-1
    Q = P[:len(transient), :len(transient)]
    I = np.eye(Q.shape[0])
    M = np.linalg.inv(I - Q)

    total_cost = sum([M[0][i] * cost[i] for i in range(len(M[0]))])
    return total_cost
