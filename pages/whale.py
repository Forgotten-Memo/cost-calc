from typing import List, Tuple
import streamlit as st
import itertools
import utils
import constants as CONST
import numpy as np
import plotly.express as px
import pandas as pd

def get_sim_results(base_cost: int, catalyst_selected: List[str], n: int = 10000) -> Tuple[List[float], List[int]]:
    results = []
    failsafes = []
    steps_history = []
    final_catalyst = catalyst_selected.pop("final", "Potent Catalyst")
    failsafe_probs = utils.modified_prob(CONST.FAILSAFES[enhancement_level], CONST.CATALYST_MODIFIERS.get(final_catalyst, lambda x: x))

    raw_probs = [CONST.CATALYST_PROB_MAP[c] for c in catalyst_selected.values()]
    costs = [CONST.CATALYST_COST_MAP[c] + base_cost for c in catalyst_selected.values()]

    for i in range(n):
        total_cost = 0
        failsafe = 0
        steps = 0

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
                rng = np.random.random()
                
                if fails[state] == 6:
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
            total_cost += CONST.CATALYST_COST_MAP[final_catalyst]
            if rng2 <= failsafe_probs[failsafe]:
                results.append(total_cost)
                failsafes.append(failsafe)
                break
            else:
                failsafe += 1
        steps_history.append(steps)
    return results, failsafes, steps_history


@st.cache_data(show_spinner=False)
def get_cached_sim_results(base_cost: int, catalyst_selected: List[str], n: int = 10000) -> Tuple[List[float], List[int]]:
    return get_sim_results(base_cost, catalyst_selected, n=n)

@st.cache_data(show_spinner=False)
def optimise(chain_length, base_cost):
    sim_params = [["No Catalyst", "Catalyst", "Potent Catalyst"]] * chain_length
    if chain_length == 3:
        sim_params[-1].append("3 Star Catalyst")
    elif chain_length == 4:
        sim_params[-1].append("4 Star Catalyst")

    permutations = list(itertools.product(*sim_params))

    min_cost = float('inf')
    min_key = None
    for i in permutations:
        raw_probs = [CONST.CATALYST_PROB_MAP[c] for c in i]
        costs = [base_cost + CONST.CATALYST_COST_MAP[c] for c in i]

        key = tuple(i)
        total_cost = utils.calc_cost(raw_probs, costs)

        if total_cost < min_cost:
            min_cost = total_cost
            min_key = key
    return min_key, min_cost

def optimise_tab(chain_length, base_cost):
    min_key, min_cost = optimise(chain_length, base_cost)

    st.subheader("Optimal Catalyst Usage")
    min_final_catalyst, min_overall_cost = None, float('inf')
    for final_catalyst in ["No Catalyst", "Catalyst", "Potent Catalyst"]:
        modifier = CONST.CATALYST_MODIFIERS.get(final_catalyst, lambda x: x)
        modified_probs = utils.modified_prob(CONST.FAILSAFES[enhancement_level], modifier)
        overall_cost = (min_cost + CONST.CATALYST_COST_MAP[final_catalyst]) / utils.cumulative_prob(modified_probs)
        if overall_cost < min_overall_cost:
            min_overall_cost = overall_cost
            min_final_catalyst = final_catalyst

    st.write(f"Average Total Cost: `{min_overall_cost:,.2f}` opals --- `{min_overall_cost / gold_market_price * 1000000:,.0f}` g")
    st.write(f"Average cost (Per failsafe): `{min_cost:,.2f}` opals --- `{min_cost / gold_market_price * 1000000:,.0f}` g")
    st.divider()

    table_data = []
    for i, k in enumerate(min_key):
        from_to = f"{'★' * i}{'☆' * (chain_length - i)} → {'★' * (i+1)}{'☆' * (chain_length - (i + 1))}"
        table_data.append({"Step": from_to, "Catalyst": f"`{k}`"})
    from_to_final = f"{'★' * chain_length} → +{enhancement_level + 1}"
    table_data.append({
        "Step": from_to_final,
        "Catalyst": f"`{min_final_catalyst}`"
    })
    st.table(pd.DataFrame(table_data))


def simulate_tab(chain_length, base_cost):
    catalyst_selected = {}
    min_key, _ = optimise(chain_length, base_cost)
    options = ["No Catalyst", "Catalyst", "Potent Catalyst"]
    for i in range(chain_length):
        if chain_length == 3 and i == 2:
            options.append("3 Star Catalyst")
        elif chain_length == 4 and i == 3:
            options.append("4 Star Catalyst")
        catalyst_selected[i] = st.selectbox(index=options.index(min_key[i]), label=f"{'★' * i}{'☆' * (chain_length - i)}", options=options)
    
    catalyst_selected["final"] = st.selectbox(index=2, label=f"{'★' * chain_length}", options=options)


    mode = st.selectbox(label="Select Simulation Mode:", options=["Single Simulation", "Distribution Simulation"])
    n = 1 if mode == 'Single Simulation' else 10000

    if st.session_state.get('enhancement_level') != enhancement_level\
            or st.session_state.get('base_cost') != base_cost\
            or st.session_state.get('catalyst_selected') != catalyst_selected\
            or st.session_state.get('mode') != mode:
        st.session_state['results'] = None
        st.session_state['failsafes'] = None

    st.session_state['catalyst_selected'] = catalyst_selected
    st.session_state['mode'] = mode
    st.session_state['enhancement_level'] = enhancement_level
    st.session_state['base_cost'] = base_cost

    if st.button("Run Simulation", type="primary"):
        with st.spinner("Running hammer simulations...", show_time=True):
            if mode == 'Single Simulation':
                results, failsafes, steps = get_sim_results(base_cost, catalyst_selected, n=n)
            else:
                results, failsafes, steps = get_cached_sim_results(base_cost, catalyst_selected, n=n)

            st.session_state['results'] = results
            st.session_state['failsafes'] = failsafes
    
    if (results := st.session_state.get('results')) and (failsafes := st.session_state.get('failsafes')):
        if mode == 'Single Simulation':
            st.subheader(f"You took: `{results[0]:,.0f}` opals (`{results[0]/gold_market_price*1000000:,.0f}` gold).")
            st.subheader(f"Taps taken: `{steps[0]}`")
            st.subheader(f"Failsafe Reached: `{CONST.FAILSAFE_TEXT[failsafes[0]]}`")
        else:
            st.subheader(f"Results from {n} simulations.")
            st.write(f"Mean: {np.mean(results):,.2f} opals")
            st.write(f"Std: {np.std(results):,.2f} opals")
            st.write(f"Min: {np.min(results):,.2f} opals")
            st.write(f"Max: {np.max(results):,.2f} opals")

            st.divider()

            percentile = st.slider(
                "Select percentile", 
                min_value=0.00, 
                max_value=1.00, 
                value=0.50, 
                step=0.01
            )
            index = int(percentile * (len(results) - 1))
            value = sorted(results)[index]

            st.write(f"Cost at `{percentile:.1%}` percentile:", f"`{value:,.2f}` opals (`{value / gold_market_price * 1000000:,.0f}` gold)")

            st.divider()

            results_df = pd.DataFrame(results, columns=["value"])
            fig = px.histogram(
                results_df,
                x="value",
                nbins=20,
                labels={"value": "Total Cost"},
                title="Simulation Results Histogram",
                histnorm="probability"
            )

            fig.update_layout(
                xaxis_title="Total Cost",
                yaxis_title="Ratio"
            )

            st.plotly_chart(fig)


st.title("CoA Hammer Calculator")
st.info("A tool to calculate how ridiculous the cost of hammering can be in CoA to help you think twice before giving your money to Glen. By シHyacine (IW01) AKA Mem0.")

enhancement_level_select = st.selectbox(label="Enhancement Level", options=[f"{i} → {i+1}" for i in range(15,25)])
enhancement_level = int(enhancement_level_select.split(" → ")[0])

### Calculate / Set Attempt Cost
st.markdown("Attempt Cost")
with st.expander(f"Calculate cost of each tap", expanded=True):
    gold_attempt_cost = st.number_input(label="Gold per tap", value=CONST.TAP_COST[enhancement_level])
    parts_attempt_cost = st.number_input(label="Cost of Spare Parts per tap", value=30000)
    attempt_cost = gold_attempt_cost + parts_attempt_cost
    st.write(f"Total Cost Per 1-tap: `{attempt_cost:,.0f}` gold")

gold_market_price = st.number_input(label="1m Gold Valuation (Opals)", min_value=100.0, max_value=1000.0, value=200.0)
base_cost = attempt_cost / 1000000 * gold_market_price

thresholds = {15: 3, 18: 4, 20: 5, 22: 6}
chain_length = None
for k, v in thresholds.items():
    if enhancement_level >= k:
        chain_length = v
    else:
        break

tab1, tab2 = st.tabs(["Optimizer", "Simulator"])

with tab1:
    optimise_tab(chain_length, base_cost)
    st.warning("Disclaimer: This optimisation assumes that you will always use the same catalyst for each stage (e.g. always using Potent Catalyst at amp 4). In reality, there may be cases you will not want to do so, e.g. when you are already at 6/6 amplification and have a guarantee regardless of whether the catalyst is used. Nevertheless, the 'improvement' in cost is generally not significant in magnitude and the results should still give a decent representation of the average costs.")

with tab2:
    simulate_tab(chain_length, base_cost)