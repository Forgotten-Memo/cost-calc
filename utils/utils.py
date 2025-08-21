import streamlit as st
import numpy as np
from typing import List, Callable
import constants as CONST

CATALYST_COST_MAP = {
    "No Catalyst": 0,
    "Catalyst": st.session_state.get('catalyst_price', 100),
    "Stable Catalyst": st.session_state.get('catalyst_price', 100) * 2,
    "Potent Catalyst": st.session_state.get('potent_catalyst_price', 800),
    "3 Star Catalyst": st.session_state.get('potent_catalyst_price', 800) * 10,
    "4 Star Catalyst": st.session_state.get('potent_catalyst_price', 800) * 40
}

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

def modified_prob(probs: List[float], modifier: Callable = lambda x: x) -> List[float]:
    """
    Applies a modifier to the expected fraction of each probability in the list.
    """
    return [modifier(p) for p in probs]

def cumulative_prob(probs: list) -> float:
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

def calc_cost(catalyst_selected: List[str], base_cost: int, CATALYST_COST_MAP: dict):
    """
    Calculates cost given a set of raw probabilities and costs.
    """
    raw_probs = [CONST.CATALYST_PROB_MAP[catalyst] for catalyst in catalyst_selected]
    P = gen_matrix(raw_probs)

    absorbing = [i for i in range(len(P)) if P[i][i] == 1 and all(P[i][j] == 0 for j in range(len(P)) if j != i)]
    transient = [i for i in range(len(P)) if i not in absorbing]

    # Compute M = (I - Q)^-1
    Q = P[:len(transient), :len(transient)]
    I = np.eye(Q.shape[0])
    M = np.linalg.inv(I - Q)

    total_cost = sum([M[0][i] * (CATALYST_COST_MAP[catalyst] + base_cost) for i, catalyst in enumerate(catalyst_selected)])
    taps = sum(M[0]) 
    catalyst_usage = {}
    for i, catalyst in enumerate(catalyst_selected):
        catalyst_usage[catalyst] = catalyst_usage.get(catalyst, 0) + M[0][i] 
    

    return total_cost, taps, catalyst_usage
