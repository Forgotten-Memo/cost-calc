from typing import List, Tuple
import streamlit as st
import itertools
import utils.utils as utils
import utils.absolute_policy as absolute_policy
import constants as CONST
import numpy as np
import plotly.express as px
import pandas as pd


CATALYST_COST_MAP = {
    "No Catalyst": 0,
    "Catalyst": st.session_state.get('catalyst_price', 100),
    "Stable Catalyst": st.session_state.get('catalyst_price', 100) * 2,
    "Potent Catalyst": st.session_state.get('potent_catalyst_price', 800),
    "3 Star Catalyst": st.session_state.get('potent_catalyst_price', 800) * 10,
    "4 Star Catalyst": st.session_state.get('potent_catalyst_price', 800) * 40
}

def get_sim_results(base_cost: int, catalyst_selected: List[str], n: int = 10000) -> Tuple[List[float], List[int]]:
    """
    Run the simulation for a given base cost and catalyst selection.
    """
    
    results = []
    failsafes = []
    steps_history = []
    final_catalyst = catalyst_selected.pop("final", "Potent Catalyst")
    failsafe_probs = utils.modified_prob(CONST.FAILSAFES[enhancement_level], CONST.CATALYST_MODIFIERS.get(final_catalyst, lambda x: x))
    catalysts_results = []

    raw_probs = [CONST.CATALYST_PROB_MAP[c] for c in catalyst_selected.values()]
    costs = [CATALYST_COST_MAP[c] + base_cost for c in catalyst_selected.values()]
    
    for i in range(n):
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
def get_cached_sim_results(base_cost: float, catalyst_selected: List[str], CATALYST_COST_MAP: dict, n: int = 1000) -> Tuple[List[float], List[int]]:
    """
    Get cached simulation results for a given base cost and catalyst selection.
    """

    return get_sim_results(base_cost=base_cost, catalyst_selected=catalyst_selected, n=n)

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
        total_cost, taps, catalyst_usage = utils.calc_cost(i, base_cost, CATALYST_COST_MAP)

        if total_cost < min_cost:
            min_cost = total_cost
            min_key = key
            min_taps = taps
            min_catalyst_usage = catalyst_usage
    return min_key, min_cost, min_taps, min_catalyst_usage

def optimise_tab(chain_length, base_cost):
    """
    Tab for running catalyst optimisations
    """

    min_key, min_cost, min_taps, catalyst_usage = optimise(base_cost, chain_length, CATALYST_COST_MAP)

    st.subheader("Simplified Optimal Policy")
    min_final_catalyst, min_overall_cost, avg_failsafes = None, float('inf'), 0
    for final_catalyst in ["No Catalyst", "Catalyst", "Potent Catalyst"]:
        modifier = CONST.CATALYST_MODIFIERS.get(final_catalyst, lambda x: x)
        modified_probs = utils.modified_prob(CONST.FAILSAFES[enhancement_level], modifier)
        overall_cost = (min_cost + CATALYST_COST_MAP[final_catalyst]) / utils.cumulative_prob(modified_probs)
        if overall_cost < min_overall_cost:
            min_overall_cost = overall_cost
            min_final_catalyst = final_catalyst
            avg_failsafes = 1 / utils.cumulative_prob(modified_probs)

    for k, v in catalyst_usage.items():
        catalyst_usage[k] = v * avg_failsafes
    catalyst_usage[min_final_catalyst] = catalyst_usage.get(min_final_catalyst, 0) + avg_failsafes
    min_overall_cost += avg_failsafes * (base_cost + CATALYST_COST_MAP[min_final_catalyst])

    st.write(f"Average Value: `{min_overall_cost:,.2f}` Opals")
    with st.container(border=True):
        st.write(f"Average Taps: `{(min_taps + 1)* avg_failsafes:,.0f}` --- (`{(min_taps + 1) * avg_failsafes * base_cost * 1000000 / st.session_state['gold_price']:,.0f}` gold)" )
        for catalyst, usage in catalyst_usage.items():
            if catalyst != "No Catalyst":
                st.write(f"{catalyst}: `{usage:.2f}` ")
    st.write(f"Average cost (Per failsafe): `{min_cost:,.2f}` opals")
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
    """Tab for running hammer simulations"""
    catalyst_selected = {}
    min_key, min_cost, min_taps, catalyst_usage = optimise(base_cost, chain_length, CATALYST_COST_MAP)
    options = ["No Catalyst", "Catalyst", "Potent Catalyst"]
    for i in range(chain_length):
        if chain_length == 3 and i == 2:
            options.append("3 Star Catalyst")
        elif chain_length == 4 and i == 3:
            options.append("4 Star Catalyst")
        catalyst_selected[i] = st.selectbox(index=options.index(min_key[i]), label=f"{'★' * i}{'☆' * (chain_length - i)}", options=options)
    
    catalyst_selected["final"] = st.selectbox(index=2, label=f"{'★' * chain_length}", options=options)

    mode = st.selectbox(label="Select Simulation Mode:", options=["Single Simulation", "Distribution Simulation"])
    n = 1 if mode == 'Single Simulation' else 1000

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
                results, failsafes, steps, catalysts_used = get_sim_results(base_cost, catalyst_selected, n=n)
            else:
                results, failsafes, steps, catalysts_used = get_cached_sim_results(base_cost, catalyst_selected, CATALYST_COST_MAP, n=n)
            
            avg_catalysts_used = {k: np.mean([c.get(k, 0) for c in catalysts_used]) for k in catalysts_used[0].keys()}
            st.session_state['catalysts_used'] = avg_catalysts_used
            st.session_state['results'] = results
            st.session_state['failsafes'] = failsafes
    
    if (results := st.session_state.get('results')):
        if mode == 'Single Simulation':
            st.subheader(f"Total Cost: `{results[0]:,.0f}` opals.")
            with st.container(border=True):
                st.write(f"Taps taken: `{steps[0]}` --- (`{steps[0] * base_cost * 1000000 / st.session_state['gold_price']:,.0f}` gold)")
                st.write("Catalysts Used:")
                for k, v in st.session_state['catalysts_used'].items():
                    if k != "No Catalyst":
                        st.write(f" - {k}: `{v:,.0f}`")
                st.write(f"Failsafe Reached: `{CONST.FAILSAFE_TEXT[failsafes[0]]}`")
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

            st.write(f"Cost at `{percentile:.1%}` percentile:", f"`{value:,.2f}` opals (`{value / st.session_state['gold_price'] * 1000000:,.0f}` gold)")

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
    gold_attempt_cost = st.number_input(label="Gold per tap", value=CONST.TAP_COST[enhancement_level], help="This defaults to the price of a lv 60 weapon tap by default. Please correct it if you are enhancing armor or different grades of weapons.")
    parts_attempt_cost = st.number_input(label="Cost of Spare Parts per tap", value=sum([i * j for i, j in zip(CONST.SPARE_PARTS_COST[enhancement_level], [100, 1500, 10000])]), help="The total cost of spare parts per tap. Please adjust to the current market value.")
    attempt_cost = gold_attempt_cost + parts_attempt_cost
    st.write(f"Total Cost Per 1-tap: `{attempt_cost:,.0f}` gold")

base_cost = attempt_cost / 1000000 * st.session_state['gold_price']

thresholds = {15: 3, 18: 4, 20: 5, 22: 6}
chain_length = None
for k, v in thresholds.items():
    if enhancement_level >= k:
        chain_length = v
    else:
        break

tab1, tab2 = st.tabs(["Optimizer", "Simulator"])

with tab1:
    advanced_mode = st.toggle("Detailed Breakdown", False, help="Advanced mode provides the absolute optimal policy for each step, while non-advanced mode provides a general policy for each amplification.")
    if advanced_mode:
        st.info("Special thanks to @wu6551 for contributing base code for the detailed optimal policy breakdown.")
        total_cost, policy, gold_tap_cost, expected_catalyst, expected_potent = absolute_policy.get_min_cost(enhancement_level, attempt_cost, st.session_state['gold_price'], CATALYST_COST_MAP)
        st.subheader("Detailed Optimal Policy")
        st.write(f"Average Opal Value: `{total_cost:,.2f}` opals ")
        with st.container(border=True):
            st.write(f"Average Taps: `{gold_tap_cost / attempt_cost:,.0f}` --- (`{gold_tap_cost:,.0f}` gold)")
            if expected_catalyst > 0:
                st.write(f"Catalyst: `{expected_catalyst:,.1f}`")
            if expected_potent > 0:
                st.write(f"Potent Catalyst: `{expected_potent:,.1f}`")
            
        with st.expander("Detailed Policy"):
            st.write(policy)
    else:
        st.warning("Disclaimer: This is a simplified policy. This optimisation assumes that you will always use the same catalyst for each stage (e.g. always using Potent Catalyst at amp 4). In reality, there may be cases you will not want to do so, e.g. when you are already at 6/6 amplification and have a guarantee regardless of whether the catalyst is used. Use the detailed policy generator for more precise recommendations at each step.")
        optimise_tab(chain_length, base_cost)
        


with tab2:
    simulate_tab(chain_length, base_cost)