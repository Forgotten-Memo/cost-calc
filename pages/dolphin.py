from typing import List, Tuple
import streamlit as st
import itertools
import utils
import constants as CONST
import numpy as np
import plotly.express as px
import pandas as pd
from constants import CATALYST_PROB_MAP, CATALYST_COST_MAP


def gen_matrix_dolphin(catalyst_selected: list[float]):
    """
    Generates probability matrix given a list of raw probabilities
    """
    probs = [CATALYST_PROB_MAP[catalyst] for catalyst in catalyst_selected]

    P = np.zeros((6, 6))
    for i in range(5):
        if i <= 2 and catalyst_selected[i] == "Stable Catalyst":
            P[i][i] = 1 - probs[i]
            P[i][i+1] = probs[i]
        else:
            P[i][max(i-1,0)] = 1 - probs[i]
            P[i][i+1] = probs[i]

    P[5][5] = 1 # absorbing state
    return P


def calc_cost_dolphin(catalyst_selected: List[float], base_cost: int, start_level: int = 13)-> float:
    """
    Calculates cost given a set of raw probabilities and costs.
    """
    P = gen_matrix_dolphin(catalyst_selected)
    cost = [CATALYST_COST_MAP[catalyst] + base_cost for catalyst in catalyst_selected]

    absorbing = [i for i in range(len(P)) if P[i][i] == 1 and all(P[i][j] == 0 for j in range(len(P)) if j != i)]
    transient = [i for i in range(len(P)) if i not in absorbing]

    # Compute M = (I - Q)^-1
    Q = P[:len(transient), :len(transient)]
    I = np.eye(Q.shape[0])
    M = np.linalg.inv(I - Q)

    start_point = start_level - 10
    total_cost = sum([M[start_point][i] * cost[i] for i in range(len(M[0]))])
    return total_cost

@st.cache_data(show_spinner=False)
def optimise(base_cost, enhancement_level):
    sim_params = [["No Catalyst", "Catalyst", "Stable Catalyst", "Potent Catalyst"]] * 5
    permutations = list(itertools.product(*sim_params))

    min_cost = float('inf')
    min_key = None
    for i in permutations:
        key = tuple(i)
        total_cost = calc_cost_dolphin(i, base_cost, enhancement_level)

        if total_cost < min_cost:
            min_cost = total_cost
            min_key = key
    return min_key, min_cost

def optimise_tab(base_cost, enhancement_level):
    min_key, min_cost = optimise(base_cost, enhancement_level)

    st.subheader("Optimal Catalyst Usage")
    st.write(f"Average Total Cost: `{min_cost:,.2f}` opals --- `{min_cost / gold_market_price * 1000000:,.0f}` g")
    st.write(f"Average cost (Per failsafe): `{min_cost:,.2f}` opals --- `{min_cost / gold_market_price * 1000000:,.0f}` g")
    st.divider()

    table_data = []
    for i, k in enumerate(min_key):
        from_to = f"+{10+i} → +{11+i}"
        table_data.append({"Step": from_to, "Catalyst": f"`{k}`"})
    st.table(pd.DataFrame(table_data))

st.title("CoA Dolphin Calculator")
st.info("A tool to calculate how ridiculous the cost of hammering can be in CoA to help you think twice before giving your money to Glen (F2p/Dolphin edition). By シHyacine (IW01) AKA Mem0.")

enhancement_level_select = st.selectbox(label="Enhancement Level", options=[f"{i} → 15" for i in range(10,15)], index=3)
enhancement_level = int(enhancement_level_select.split(" → ")[0])


### Calculate / Set Attempt Cost
st.markdown("Attempt Cost")
with st.expander(f"Calculate cost of each tap", expanded=True):
    gold_attempt_cost = st.number_input(label="Gold per tap", value=120000)
    parts_attempt_cost = st.number_input(label="Cost of Spare Parts per tap", value=10000)
    attempt_cost = gold_attempt_cost + parts_attempt_cost
    st.write(f"Total Cost Per 1-tap: `{attempt_cost:,.0f}` gold")

gold_market_price = st.number_input(label="Opal cost per 1m gold", value=200.0)
base_cost = attempt_cost / 1000000 * gold_market_price

optimise_tab(base_cost, enhancement_level)