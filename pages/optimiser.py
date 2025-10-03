from typing import List, Tuple
import streamlit as st
import itertools
import utils.utils as utils
from utils.absolute_policy import process_policy, replace_stars
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

def highlight_potent(value):
    if value == "Potent Catalyst":
        return "<span style='color:orange; font-weight:bold;'>Potent Catalyst</span>"
    elif value == "Catalyst":
        return "<span style='color:pink; font-weight:bold;'>Catalyst</span>"
    elif value in ("3 Star Catalyst", "4 Star Catalyst"):
        return f"<span style='color:red; font-weight:bold;'>{value}</span>"
    elif value == "Stable Catalyst":
        return "<span style='color:purple; font-weight:bold;'>Stable Catalyst</span>"
    elif not value:
        value = ""
    return value

################################



st.title("CoA Enhancement Calculator")
with st.container(border=True):
    st.write("A tool to optimise and calculate how ridiculous the cost of enhancement can be in CoA to help you think twice before giving your money to Glen. By シHyacine (IW01) @forgotten_memo.")

#[f"{i} → 15" for i in range(10,15)] + 
### Configuration Display
with st.container(border=True):
    st.subheader("Configuration")
    enhancement_level_select = st.selectbox(label="Enhancement Level", options=[f"{i} → {i+1}" for i in range(15,25)])
    enhancement_level = int(enhancement_level_select.split(" → ")[0])
    
    if enhancement_level >= 15:
        cols = st.columns(3)
        current_failsafe = cols[0].number_input(label="Current Failsafe", min_value=0, max_value=6, value=3, key="failsafe", help="Current failsafe")
        current_amp_str = cols[1].selectbox(label="Current Amp", options=[replace_stars(i, enhancement_level) for i in range(CONST.AMP_THRESHOLDS[enhancement_level] + 1)], help="Current amplification level")
        current_amp = current_amp_str.count("★")
        if current_amp != CONST.AMP_THRESHOLDS[enhancement_level]:
            current_pity_str = cols[2].selectbox(label="Current Amp Pity", options=[f"{i}/6" for i in range(7)], help="Current amplification pity")
            current_pity = int(current_pity_str.split("/")[0])
        else:
            current_pity = 0

    start_index = (current_failsafe, current_amp, current_pity)

    with st.expander(f"Attempt Cost", expanded=False):
        gold_attempt_cost = st.number_input(label="Gold per tap", value=CONST.TAP_COST[enhancement_level], help="This defaults to the price of a lv 60 weapon tap by default. Please correct it if you are enhancing armor or different grades of weapons.")
        parts_attempt_cost = st.number_input(label="Cost of Spare Parts per tap", value=sum([i * j for i, j in zip(CONST.SPARE_PARTS_COST[enhancement_level], [100, 1500, 10000])]), help="The total cost of spare parts per tap. Please adjust to the current market value.")
        attempt_cost = gold_attempt_cost + parts_attempt_cost
        st.write(f"Total Cost Per 1-tap: `{attempt_cost:,.0f}` gold")

    with st.expander(f"Options", expanded=False):
        hidden_rates_toggle = st.toggle("Hidden Rate", True, help="Whether to account for hidden rates at 4/6 and 5/6 amplification. This is highly recommended to make calculations more reflective of reality.")

base_cost = attempt_cost / 1000000 * st.session_state['gold_price']
chain_length = CONST.AMP_THRESHOLDS[enhancement_level]

st.subheader("Detailed Optimal Policy")
st.info("Special thanks to @wu6551 for the collaboration on the detailed optimal policy breakdown.")

total_cost, policy, gold_tap_cost, expected_catalyst, expected_potent = absolute_policy.get_min_cost(enhancement_level, attempt_cost, st.session_state['gold_price'], CATALYST_COST_MAP, hidden_rates=hidden_rates_toggle, start_state=start_index)

st.write(f"Average Opal Value: `{total_cost:,.2f}` opals ")
with st.container(border=True):
    st.write(f"Average Taps: `{gold_tap_cost / attempt_cost:,.0f}` --- (`{gold_tap_cost:,.0f}` gold)")
    if expected_catalyst > 0:
        st.write(f"Catalyst: `{expected_catalyst:,.1f}`")
    if expected_potent > 0:
        st.write(f"Potent Catalyst: `{expected_potent:,.1f}`")
    
with st.expander("Optimal Policy"):
    tabs = st.tabs(["Pivot Table", "Raw Results"])
    data = process_policy(policy, enhancement_level)[CONST.FAILSAFE_TEXT[0]]
    with tabs[0]:
        table_data = []
        for k, v in data.items():
            print(k.split(" "))
            if " → "in k:
                stars, pity = k.split(" → ")
            else:
                stars, pity = k.split(" ")
        
            table_data.append({
                "Stars": stars,
                "Pity": pity.strip("()"), 
                "Catalyst": highlight_potent(v)
            })
        df = pd.DataFrame(table_data)
        pivot_df = df.pivot(index="Stars", columns="Pity", values="Catalyst").fillna("")
        pivot_df.columns.name = None
        pivot_df = pivot_df.reset_index()
        st.markdown(pivot_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        

    with tabs[1]:
        st.write(data)
