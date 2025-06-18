import streamlit as st
import itertools
import utils
import constants as CONST
import numpy as np
import plotly.express as px
import pandas as pd

st.title("Calculator / Simulator")

enhancement_level = st.selectbox(label="Enhancement Level", options=list(range(15,25)))
attempt_cost = st.number_input(label="Gold per attempt", value=300000)
gold_market_price = st.number_input(label="Opal cost per 1m gold", value=178.0)
base_cost = attempt_cost / 1000000 * gold_market_price

thresholds = {15: 3, 18: 4, 20: 5, 22: 6}
chain_length = None
for k, v in thresholds.items():
    if enhancement_level >= k:
        chain_length = v
    else:
        break

tab1, tab2 = st.tabs(["Optimizer", "Simulator"])

def optimise():
    sim_params = [["No Catalyst", "Catalyst", "Potent Catalyst"]] * chain_length
    permutations = list(itertools.product(*sim_params))

    results = {}
    min_cost = float('inf')
    min_key = None

    for i in permutations:
        raw_probs = [CONST.CATALYST_PROB_MAP[c] for c in i]
        costs = [base_cost + CONST.CATALYST_COST_MAP[c] for c in i]

        key = tuple(i)
        total_cost = utils.calc_cost(raw_probs, costs)

        results[key] = total_cost

        if total_cost < min_cost:
            min_cost = total_cost
            min_key = key

    st.subheader("Optimal Catalyst Usage")
    overall_cost = min_cost / utils.cumulative_prob(CONST.FAILSAFES[enhancement_level]) + 800 / utils.cumulative_prob(CONST.FAILSAFES[enhancement_level])
    st.write(f"Average Total Cost: `{overall_cost:.2f}` opals --- `{overall_cost / gold_market_price * 1000000:,.0f}` g")
    st.write(f"Average cost (Per failsafe): `{min_cost:.2f}` opals --- `{min_cost / gold_market_price * 1000000:,.0f}` g")
    st.divider()

    for i, k in enumerate(min_key):
        current = f"{'★' * i}{'☆' * (chain_length - i)}"
        next = f"{'★' * (i+1)}{'☆' * (chain_length - (i + 1))}"
        st.write(f"{current} -> {next} - {k}")


def simulate():
    catalyst_selected = {}
    for i in range(chain_length):
        catalyst_selected[i] = st.selectbox(label=f"{'★' * i}{'☆' * (chain_length - i)}", options=["No Catalyst", "Catalyst", "Potent Catalyst"])

    mode = st.selectbox(label="Select Simulation Mode:", options=["Single Simulation", "Distribution Simulation"])
    n = 1 if mode == 'Single Simulation' else 10000
    if st.button("Run Simulation", type="primary"):
        def get_sim_results(n=10000):
            results = []
            failsafes = []
            raw_probs = [CONST.CATALYST_PROB_MAP[c] for c in catalyst_selected.values()]
            costs = [CONST.CATALYST_COST_MAP[c] + base_cost for c in catalyst_selected.values()]

            
            for i in range(n):
                total_cost = 0
                failsafe = 0
                steps = 0

                if len(raw_probs) != len(costs):
                    raise ValueError("raw_probs and cost must have the same length")
                while failsafe < 7:
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
                    total_cost += 800
                    if rng2 <= CONST.FAILSAFES[enhancement_level][failsafe]:
                        results.append(total_cost)
                        failsafes.append(failsafe)
                        break
                    else:
                        failsafe += 1
            return results, failsafes

        results, failsafes = get_sim_results(n=n)
        
        if mode == 'Single Simulation':
            st.subheader(f"You took: `{results[0]:,.0f}` opals (`{results[0]/gold_market_price*1000000:,.0f}` gold) for a successful enhancement. `{failsafes[0]}` failsafe attempts.")
        else:
            st.subheader(f"Results from {n} simulations.")
            st.write(f"Mean: {np.mean(results):,.2f}")
            st.write(f"Std: {np.std(results):,.2f}")
            st.write(f"Min: {np.min(results):,.2f}")
            st.write(f"Max: {np.max(results):,.2f}")

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

        

with tab1:
    optimise()

with tab2:
    simulate()
