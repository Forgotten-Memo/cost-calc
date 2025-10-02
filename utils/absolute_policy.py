import numpy as np
from itertools import product
from typing import List, Literal, Tuple
import streamlit as st
import constants as CONST

def cartesian_product(list_of_spaces):
    return list(product(*list_of_spaces))

# Define states and actions
def get_states(n: int):
    """
    Generate all possible states based on the number of enhancements.
    
    Args:
        n (int): The number of enhancement levels.
        
    Returns:
        list: A list of tuples representing all possible states.
    """
    amp_levels = list(range(n+1))
    failsafe_levels = (0, 1, 2, 3, 4, 5, 6)
    
    # States is a cartesian product of enhancement levels and failsafe levels for each enhancement level except the terminal
    states = cartesian_product([amp_levels] + [failsafe_levels] * (n+1))
    
    return states

# Actions are potential actions
ACTIONS = Literal["No Catalyst", "Catalyst", "Potent Catalyst", "3 Star Catalyst", "4 Star Catalyst", "do nothing"]

def get_R(cost_per_tap_in_gold: int, gems_per_1m: float, catalyst_cost_map: dict, reference_frame: str = "OPALS"):
    if reference_frame == "OPALS":
        cost_per_tap = cost_per_tap_in_gold/1_000_000*gems_per_1m
    elif reference_frame == "GOLD":
        cost_per_tap = cost_per_tap_in_gold

    if reference_frame == "OPALS":
        multiplier = 1.0
    elif reference_frame == "GOLD":
        multiplier = 1_000_000 / (gems_per_1m)

    R = {
        "No Catalyst": cost_per_tap,
        "Catalyst": cost_per_tap + catalyst_cost_map['Catalyst'] * multiplier,
        "Potent Catalyst": cost_per_tap + catalyst_cost_map['Potent Catalyst'] * multiplier,
        "3 Star Catalyst": cost_per_tap + catalyst_cost_map['3 Star Catalyst'] * multiplier,
        "4 Star Catalyst": cost_per_tap + catalyst_cost_map['4 Star Catalyst'] * multiplier,
        "do nothing": 0.0
    }
    return R

def get_possible_actions(current_amp: int, n: int):
    """
    Determines the possible catalyst actions for a given amplification state and enhancement level.
    Args:
        current_amp (int): The current amplification stage (e.g., 2 for 3*, 3 for 4*).
        n (int): The number of amps
    Returns:
        tuple: A tuple of strings representing the possible catalyst actions, which may include:
            - "No Catalyst"
            - "Catalyst"
            - "Potent Catalyst"
            - "3 Star Catalyst" (if n == 3 and current_amp == 2)
            - "4 Star Catalyst" (if n == 4 and current_amp == 3)
    """
    
    actions_possible = ["No Catalyst", "Catalyst", "Potent Catalyst"]

    # For enhancement levels 15-17, we allow amplification guarantee at 3*
    if n == 3 and current_amp == 2:
        actions_possible.append("3 Star Catalyst")

    # For enhancement levels 18-19, we allow amplification guarantee at 4*
    if n == 4 and current_amp == 3:
        actions_possible.append("4 Star Catalyst")

    return tuple(actions_possible)

def get_probability_matrix(current_level: int, hidden_rates: bool = True):
    """
    Generate the probability matrix for a given enhancement level and number of enhancements.
    Args:
        current_level (int): The current enhancement level.
        hidden_rates (bool): Whether to account for hidden rates at 4/6 and 5/6 amplification.
    """
    # Define P_a(fail, s)
    P = {}
    AMAX = CONST.AMP_THRESHOLDS[current_level]
    for f in range(7):
        for amp in range(AMAX+1):
            # Handle success probability for final amp level
            if amp == AMAX:
                base_success_chance = CONST.FAILSAFES[current_level][f]
                possible_actions = get_possible_actions(amp, AMAX)
                for action in possible_actions:
                    adjusted_probability = CONST.CATALYST_MODIFIERS[action](base_success_chance)
                    P[(action, f, amp, 0)] = adjusted_probability
            else:
                for pity in range(7):
                    if pity == 6:
                        base_success_chance = 1.0
                    elif hidden_rates and (pity in (4, 5)):
                        base_success_chance = 0.5
                    else:
                        base_success_chance = 0.2

                    possible_actions = get_possible_actions(amp, AMAX)
                    for action in possible_actions:
                        adjusted_probability = CONST.CATALYST_MODIFIERS[action](base_success_chance)
                        P[(action, f, amp, pity)] = adjusted_probability

    return P

def replace_stars(key: Tuple[int, int] | int, enhancement_level: int) -> str:
    """
    Replaces policy key with stars.

    Args:
        key Tuple[int, int]: The key representing the amplification and pity counter.
        n (int): The total number of amplifications.
    """
    n = CONST.AMP_THRESHOLDS[enhancement_level]
    if isinstance(key, int):
        a = key
        black_stars = "★" * a
        white_stars = "☆" * (n-a)
        return f'{black_stars}{white_stars}'
    else:
        a, p = key
        black_stars = "★" * a
        white_stars = "☆" * (n-a)
        if a == n:
            return f'{black_stars} → +{enhancement_level + 1}'

        return f'{black_stars}{white_stars} ({p}/6)'

def process_policy(policy: np.ndarray, enhancement_level: int):
    updated_policy = {CONST.FAILSAFE_TEXT[fs]: {} for fs in range(7)}
    for k, v in sorted(list(np.ndenumerate(policy)), key=lambda item: str(item[0])):
        f, a, p = k
        if v:
            updated_policy[CONST.FAILSAFE_TEXT[f]][replace_stars((a, p), enhancement_level)] = v
    return updated_policy

def get_success_path(start_state: Tuple[int, int, int], n: int) -> List[Tuple[int, int, int]]:
    f, a, p = start_state
    path = [(f,a,p)]
    while a < n:
        a += 1
        path.append((f, a, 0))
    
    return path


def get_min_cost(current_level: int, cost_per_tap_in_gold: int, gems_per_1m: float, catalyst_cost_map: dict, reference_frame: str = "OPALS", hidden_rates: bool = True, start_state: Tuple[int, int, int]=(0,0,0)):
    AMAX = CONST.AMP_THRESHOLDS[current_level]
    PMAX = 6
    FMAX = 6
    P = get_probability_matrix(current_level, hidden_rates)
    R = get_R(cost_per_tap_in_gold, gems_per_1m, catalyst_cost_map, reference_frame)

    X = np.full((FMAX+1, AMAX+1, PMAX+1), np.inf)
    policy = np.empty((FMAX+1, AMAX+1, PMAX+1), dtype=object)
    expected_taps = np.full((FMAX+1, AMAX+1, PMAX+1), 0.0)
    expected_catalyst = np.full((FMAX+1, AMAX+1, PMAX+1), 0.0)
    expected_potent = np.full((FMAX+1, AMAX+1, PMAX+1), 0.0)

    f=0
    for f in reversed(range(FMAX+1)):
        for a in range(AMAX+1):
            for p in reversed(range(PMAX+1)):
                if a == AMAX:
                    if f == FMAX:
                        X[(f,a,0)] = R["No Catalyst"]
                        policy[(f,a,0)] = "No Catalyst"
                        expected_taps[(f,a,0)] = 1
                        expected_catalyst[(f,a,0)] = 0
                        expected_potent[(f,a,0)] = 0
                    elif p == 0:
                        cost_if_fail = 0
                        fail_taps = 0
                        fail_catalysts_used = 0
                        fail_potents_used = 0
    
                        for k in range(a+1): # Need to go through success chain of f+1 if fail.
                            cost_if_fail += X[(f+1, k, 0)]
                            fail_taps += expected_taps[(f+1, k, 0)]
                            fail_catalysts_used += expected_catalyst[(f+1, k, 0)]
                            fail_potents_used += expected_potent[(f+1, k, 0)]

                        for action in get_possible_actions(a, AMAX):
                            p_success = P[(action,f,a,p)]
                            cost_under_action = R[action] + (1-p_success) * cost_if_fail
                            taps_under_action = 1 + (1-p_success) * fail_taps
                            if action == "Catalyst":
                                catalysts_under_action = 1 + (1-p_success) * fail_catalysts_used
                            else:
                                catalysts_under_action = (1-p_success) * fail_catalysts_used

                            if action == "Potent Catalyst":
                                potents_under_action = 1 + (1-p_success) * fail_potents_used
                            elif action == "3 Star Catalyst":
                                potents_under_action = 10 + (1-p_success) * fail_potents_used
                            elif action == "4 Star Catalyst":
                                potents_under_action = 40 + (1-p_success) * fail_potents_used
                            else:
                                potents_under_action = (1-p_success) * fail_potents_used

                            if cost_under_action <= X[(f,a,p)]:
                                X[(f,a,p)] = cost_under_action
                                policy[(f,a,p)] = action
                                expected_taps[(f,a,p)] = taps_under_action
                                expected_catalyst[(f,a,p)] = catalysts_under_action
                                expected_potent[(f,a,p)] = potents_under_action

                elif p == 6:
                    X[(f,a,p)] = R["No Catalyst"]
                    policy[(f,a,p)] = "No Catalyst"
                    expected_taps[(f,a,p)] = 1
                    expected_catalyst[(f,a,p)] = 0
                    expected_potent[(f,a,p)] = 0
                else:
                    cost_if_fail = 0
                    fail_taps = 0
                    fail_catalysts_used = 0
                    fail_potents_used = 0

                    for k in range(a):
                        cost_if_fail += X[(f,k,0)]
                        fail_taps += expected_taps[(f,k,0)]
                        fail_catalysts_used += expected_catalyst[(f,k,0)]
                        fail_potents_used += expected_potent[(f,k,0)]

                    cost_if_fail += X[(f, a, p+1)]
                    fail_taps += expected_taps[(f, a, p+1)]
                    fail_catalysts_used += expected_catalyst[(f, a, p+1)]
                    fail_potents_used += expected_potent[(f, a, p+1)]

                    for action in get_possible_actions(a, AMAX):
                        p_success = P[(action,f,a,p)]
                        cost_under_action = R[action] + (1-p_success) * cost_if_fail
                        taps_under_action = 1 + (1-p_success) * fail_taps

                        if action == "Catalyst":
                            catalysts_under_action = 1 + (1-p_success) * fail_catalysts_used
                        else:
                            catalysts_under_action = (1-p_success) * fail_catalysts_used

                        if action == "Potent Catalyst":
                            potents_under_action = 1 + (1-p_success) * fail_potents_used
                        elif action == "3 Star Catalyst":
                            potents_under_action = 10 + (1-p_success) * fail_potents_used
                        elif action == "4 Star Catalyst":
                            potents_under_action = 40 + (1-p_success) * fail_potents_used
                        else:
                            potents_under_action = (1-p_success) * fail_potents_used


                        if cost_under_action <= X[(f,a,p)]:
                            X[(f,a,p)] = cost_under_action
                            policy[(f,a,p)] = action
                            expected_taps[(f,a,p)] = taps_under_action
                            expected_catalyst[(f,a,p)] = catalysts_under_action
                            expected_potent[(f,a,p)] = potents_under_action

    total_cost = 0
    total_taps = 0
    catalyst_cost = 0
    potent_cost = 0

    success_path = get_success_path(start_state, AMAX)

    for idx in success_path:
        total_cost += X[idx]
        total_taps += expected_taps[idx]
        catalyst_cost += expected_catalyst[idx]
        potent_cost += expected_potent[idx]

    if reference_frame == "OPALS":
        opals_used_for_gold = total_cost - catalyst_cost  * catalyst_cost_map['Catalyst'] - potent_cost * catalyst_cost_map['Potent Catalyst']
        gold_tap_cost = opals_used_for_gold/gems_per_1m * 1_000_000
    elif reference_frame == "GOLD":
        total_opals_used_for_catalyst = catalyst_cost  * catalyst_cost_map['Catalyst'] + potent_cost * catalyst_cost_map['Potent Catalyst']
        gold_tap_cost = (total_cost - total_opals_used_for_catalyst) / gems_per_1m * 1000000

    return total_cost, policy, gold_tap_cost, catalyst_cost, potent_cost