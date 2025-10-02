
import streamlit as st
import utils.utils as utils
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

@st.dialog("Rates for Enhancement", width="large")
def show_rates():
    st.subheader("Failsafe Rates")
    data = [
        {"Level": lvl, **{f"Failsafe {i}": val for i, val in enumerate(vals)}}
        for lvl, vals in CONST.FAILSAFES.items()
    ]
    df = pd.DataFrame(data)
    pivot_df = df.pivot_table(index='Level', values=[f"Failsafe {i}" for i in range(7)])
    pivot_df = pivot_df.applymap(lambda x: f"{x:.2f}" if isinstance(x, float) else x)
    st.dataframe(pivot_df, use_container_width=True)



def simulate_tab(enhancement_level: int, base_cost: float, hidden_r: bool, multi: int = 1000):
    """Tab for running hammer simulations"""
    mode = st.selectbox(label="Select Simulation Mode:", options=["Single Simulation", "Distribution Simulation"])
    n = 1 if mode == 'Single Simulation' else multi

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
                results, failsafes, steps, catalysts_used = utils.get_sim_results(enhancement_level, base_cost, catalyst_selected, n=n, hidden_r=hidden_r)
            else:
                results, failsafes, steps, catalysts_used = utils.get_cached_sim_results(enhancement_level, base_cost, catalyst_selected, CATALYST_COST_MAP, n=n, hidden_r=hidden_r)
            
            avg_catalysts_used = {k: np.mean([c.get(k, 0) for c in catalysts_used]) for k in catalysts_used[0].keys()}
            st.session_state['catalysts_used'] = avg_catalysts_used
            st.session_state['results'] = results
            st.session_state['failsafes'] = failsafes
            st.session_state['steps'] = steps
    
    if (results := st.session_state.get('results')) and (steps := st.session_state.get('steps')) and (failsafes := st.session_state.get('failsafes')):
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
            cols = st.columns(2)
            with cols[0]:
                st.subheader(f"Simulation Results")
                st.write(f"n = `{len(results)}` simulations")
                st.write(f"Average Taps: `{np.mean(steps):,.0f}` --- (`{np.mean(steps) * base_cost * 1000000 / st.session_state['gold_price']:,.0f}` gold)")
                
                
                st.write(f"Mean: `{np.mean(results):,.2f}` opals")
                st.write(f"Std: `{np.std(results):,.2f}` opals")
                st.write(f"Min: `{np.min(results):,.2f}` opals")
                st.write(f"Max: `{np.max(results):,.2f}` opals")

            with cols[1]:
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

            st.divider()

            st.subheader("Percentile Calculator")

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


################################



st.title("CoA Enhancement Simulator")
with st.container(border=True):
    st.write("A tool to simulate how ridiculous the cost of enhancement can be in CoA to help you think twice before giving your money to Glen. By シHyacine (IW01) @forgotten_memo.")


### Configuration Display
with st.container(border=True):
    st.subheader("Configuration")
    enhancement_level_select = st.selectbox(label="Enhancement Level", options=[f"{i} → {i+1}" for i in range(15,25)])
    enhancement_level = int(enhancement_level_select.split(" → ")[0])

    with st.expander(f"Attempt Cost", expanded=False):
        gold_attempt_cost = st.number_input(label="Gold per tap", value=CONST.TAP_COST[enhancement_level], help="This defaults to the price of a lv 60 weapon tap by default. Please correct it if you are enhancing armor or different grades of weapons.")
        parts_attempt_cost = st.number_input(label="Cost of Spare Parts per tap", value=sum([i * j for i, j in zip(CONST.SPARE_PARTS_COST[enhancement_level], [100, 1500, 10000])]), help="The total cost of spare parts per tap. Please adjust to the current market value.")
        attempt_cost = gold_attempt_cost + parts_attempt_cost
        st.write(f"Total Cost Per 1-tap: `{attempt_cost:,.0f}` gold")

    base_cost = attempt_cost / 1000000 * st.session_state['gold_price']
    chain_length = CONST.AMP_THRESHOLDS[enhancement_level]

    with st.expander(f"Catalyst Selection", expanded=True):
        catalyst_selected = {}
        min_key, min_cost, min_taps, catalyst_usage = utils.optimise(base_cost, chain_length, CATALYST_COST_MAP)
        options = ["No Catalyst", "Catalyst", "Potent Catalyst"]
        extra_options = []
        for i in range(chain_length):
            if chain_length == 3 and i == 2:
                extra_options = ["3 Star Catalyst"]
            elif chain_length == 4 and i == 3:
                extra_options = ["4 Star Catalyst"]
            
            concat_options = options + extra_options
            catalyst_selected[i] = st.selectbox(index=concat_options.index(min_key[i]), label=f"{'★' * i}{'☆' * (chain_length - i)}", options=concat_options)

        catalyst_selected["final"] = st.selectbox(index=2, label=f"{'★' * chain_length}", options=options)

    with st.expander(f"Options", expanded=False):
        hidden_rates_toggle = st.toggle("Hidden Rate", True, help="Whether to account for hidden rates at 4/6 and 5/6 amplification. This is highly recommended to make calculations more reflective of reality.")
        n_sims = st.number_input(label="Number of Simulations", min_value=1, max_value=10000, value=1000 if st.session_state.get('mode') == 'Distribution Simulation' else 1, step=1, help="Number of simulations to run. Higher numbers give more accurate results but take longer.")

    if st.button("Show Enhancement Rates"):
        show_rates()


simulate_tab(enhancement_level, base_cost, hidden_rates_toggle, n_sims)


