import numpy as np
from itertools import product
from typing import Literal, List
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

def get_probability_matrix(current_level: int):
    """
    Generate the probability matrix for a given enhancement level and number of enhancements.
    Args:
        current_level (int): The current enhancement level.
    """
    # Define P_a(fail, s)
    P = {}
    n = CONST.AMP_THRESHOLDS[current_level]
    amp_levels = list(range(n+1))
    for i in amp_levels:
        for f in range(7):
            # Handle success probability for final amp level
            if i == amp_levels[-1]:
                base_success_chance = CONST.FAILSAFES[current_level][f]
            else:
                base_success_chance = 0.2
            possible_actions = get_possible_actions(i, f)
            for action in possible_actions:
                adjusted_probability = min(CONST.CATALYST_MODIFIERS[action](base_success_chance),1.0)
                P[(action, i, f)] = adjusted_probability
    return P

def get_min_cost(current_level: int, cost_per_tap_in_gold: int, gems_per_1m: float, catalyst_cost_map: dict, reference_frame: str = "OPALS"):
    # X(i, i+1, f_i)
    # X stores the cost to go from i -> i+1 given that the failsafe level at i is f_i
    
    n = CONST.AMP_THRESHOLDS[current_level]
    amp_levels = list(range(n+1))
    P = get_probability_matrix(current_level)
    R = get_R(cost_per_tap_in_gold, gems_per_1m, catalyst_cost_map, reference_frame)

    X = {} # dynamic dict
    policy = {}
    expected_catalyst = {}
    expected_potent = {}
    for i in amp_levels:
        for f in range(7):
            failsafe_level = 6-f
            if failsafe_level == 6:
                # Gaurantee to go from i -> i+1
                X[(i,failsafe_level)] = R["No Catalyst"]
                policy[(i, failsafe_level)] = "No Catalyst"
                expected_catalyst[(i, failsafe_level)] = 0
                expected_potent[(i, failsafe_level)] = 0
            else:
                # X[i,f] = minimum over actions a: Cost(a) + P_a(fail|failsafe level) * (X[0,0] + X[1,0] +... + X[i-1, 0] + X[i, f+1])
                min_cost = np.inf

                # Compute X[0,0] + ... + X[i-1, 0] + X[i, f+1]
                cost_if_fail = 0
                pinks_used_if_fail = 0
                potents_used_if_fail = 0
                for k in range(0, i):
                    cost_if_fail += X[(k, 0)]
                    pinks_used_if_fail += expected_catalyst[(k, 0)]
                    potents_used_if_fail += expected_potent[(k, 0)]
                cost_if_fail += X[(i, failsafe_level+1)]
                pinks_used_if_fail += expected_catalyst[(i, failsafe_level+1)]
                potents_used_if_fail += expected_potent[(i, failsafe_level+1)]

                for action in get_possible_actions(i, failsafe_level):

                    pinks_used = 0
                    potents_used = 0
                    if action == 'Catalyst':
                        pinks_used = 1
                    elif action == 'Potent':
                        potents_used = 1
                    elif action == '3 Star Catalyst':
                        potents_used = 10
                    elif action == '4 Star Catalyst':
                        potents_used = 40

                    p_success = P[(action, i, failsafe_level)]
                    cost_under_action = R[action] + (1-p_success) * cost_if_fail
                    pinks_under_action = pinks_used + (1-p_success) * pinks_used_if_fail
                    potents_under_action = potents_used + (1-p_success) * potents_used_if_fail
                    min_cost = min(min_cost, cost_under_action)
                    if cost_under_action <= min_cost:
                        min_cost = cost_under_action
                        policy[(i, failsafe_level)] = action
                        expected_catalyst[(i, failsafe_level)] = pinks_under_action
                        expected_potent[(i, failsafe_level)] = potents_under_action

                X[(i,failsafe_level)] = min_cost


    total_cost = 0
    pink_cost = 0
    potent_cost = 0
    for i in range(n+1):
        total_cost += X[(i,0)]
        pink_cost += expected_catalyst[(i,0)]
        potent_cost += expected_potent[(i,0)]

    if reference_frame == "OPALS":
        opals_used_for_gold = total_cost - pink_cost  * catalyst_cost_map['Catalyst'] - potent_cost * catalyst_cost_map['Potent Catalyst']
        gold_tap_cost = opals_used_for_gold/gems_per_1m * 1_000_000
    elif reference_frame == "GOLD":
        total_opals_used_for_catalyst = pink_cost  * catalyst_cost_map['Catalyst'] + potent_cost * catalyst_cost_map['Potent Catalyst']
        gold_tap_cost = (total_cost - total_opals_used_for_catalyst) / gems_per_1m * 1000000

    policy = {str(k): v for k, v in sorted(policy.items(), key=lambda item: str(item[0]))}
    return total_cost, policy, gold_tap_cost, pink_cost, potent_cost

