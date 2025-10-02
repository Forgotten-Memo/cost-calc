import streamlit as st
import numpy as np
from typing import List, Callable, Tuple
import constants as CONST
import itertools

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

@st.cache_data(show_spinner=False)
def optimise(base_cost: float, chain_length: int, CATALYST_COST_MAP: dict):
    """
    Optimise the catalyst usage for a given chain length and base cost.
    """

    sim_params = [["No Catalyst", "Catalyst", "Potent Catalyst"]] * chain_length
    if chain_length == 3:
        sim_params[-1].append("3 Star Catalyst")
    elif chain_length == 4:
        sim_params[-1].append("4 Star Catalyst")

    permutations = list(itertools.product(*sim_params))

    min_cost = float('inf')
    min_key = None
    min_taps = None
    min_catalyst_usage = None

    for i in permutations:
        key = tuple(i)
        total_cost, taps, catalyst_usage = calc_cost(i, base_cost, CATALYST_COST_MAP)

        if total_cost < min_cost:
            min_cost = total_cost
            min_key = key
            min_taps = taps
            min_catalyst_usage = catalyst_usage
    return min_key, min_cost, min_taps, min_catalyst_usage


def get_sim_results(enhancement_level: int, base_cost: int,  catalyst_selected: List[str], n: int = 10000, hidden_r: bool=True) -> Tuple[List[float], List[int]]:
    """
    Run the simulation for a given base cost and catalyst selection.
    """
    
    results = []
    failsafes = []
    steps_history = []
    final_catalyst = catalyst_selected.pop("final", "Potent Catalyst")
    failsafe_probs = modified_prob(CONST.FAILSAFES[enhancement_level], CONST.CATALYST_MODIFIERS.get(final_catalyst, lambda x: x))
    catalysts_results = []

    raw_probs = [CONST.CATALYST_PROB_MAP[c] for c in catalyst_selected.values()]
    costs = [CATALYST_COST_MAP[c] + base_cost for c in catalyst_selected.values()]
    
    for _ in range(n):
        total_cost = 0
        failsafe = 0
        steps = 0
        catalysts_used = {}

        if len(raw_probs) != len(costs):
            raise ValueError("raw_probs and cost must have the same length")
        while failsafe < 7:
            steps += 1
            max_state = len(raw_probs)
            state = 0
            fails = [0] * max_state
            
            while state != max_state:
                probs = raw_probs[state]
                total_cost += costs[state]
                catalysts_used[catalyst_selected[state]] = catalysts_used.get(catalyst_selected[state], 0) + 1
                rng = np.random.random()
                
                if fails[state] == 6:
                    next_state = state + 1
                    fails[state] = 0
                elif fails[state] in (4, 5) and hidden_r and rng <= CONST.CATALYST_MODIFIERS[catalyst_selected[state]](0.5):
                    next_state = state + 1
                    fails[state] = 0
                elif rng <= probs:
                    next_state = state + 1
                    fails[state] = 0
                else:
                    next_state = 0
                    fails[state] += 1
                
                state = next_state
                steps += 1
            
            rng2 = np.random.random()
            total_cost += CATALYST_COST_MAP[final_catalyst] + base_cost # Failsafe tap
            catalysts_used[final_catalyst] = catalysts_used.get(final_catalyst, 0) + 1

            if rng2 <= failsafe_probs[failsafe]:
                results.append(total_cost)
                failsafes.append(failsafe)
                catalysts_results.append(catalysts_used)
                break
            else:
                failsafe += 1
        steps_history.append(steps)
    return results, failsafes, steps_history, catalysts_results


@st.cache_data(show_spinner=False)
def get_cached_sim_results(enhancement_level: int, base_cost: float, catalyst_selected: List[str], CATALYST_COST_MAP: dict, n: int = 1000, hidden_r: bool = True) -> Tuple[List[float], List[int]]:
    """
    Get cached simulation results for a given base cost and catalyst selection.
    """

    return get_sim_results(enhancement_level=enhancement_level, base_cost=base_cost, hidden_r=hidden_r, catalyst_selected=catalyst_selected, n=n)