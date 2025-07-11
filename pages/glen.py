import streamlit as st
import constants as CONST 
import numpy as np 
import time
import logging

st.title("Glen Casino (BETA)")
st.info("Enhancement casino that is free.")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


st.session_state.setdefault("enhancement_level", 15)
st.session_state.setdefault("glen_taps", 0)
st.session_state.setdefault("glen_gold", 0)
st.session_state.setdefault("glen_failsafe", 0)
st.session_state.setdefault('glen_catalysts', { "No Catalyst": 0, "Catalyst": 0, "Stable Catalyst": 0, "Potent Catalyst": 0 })
st.session_state.setdefault("glen_complete", False)
st.session_state.setdefault("notification", [])


def get_prob(enhancement_level, catalyst_usage, current_failsafe):
    if st.session_state["glen_current_amp"] == len(amps):
        return CONST.CATALYST_MODIFIERS.get(catalyst_usage, lambda x: x)(CONST.FAILSAFES[enhancement_level][current_failsafe])
    else:

        return CONST.CATALYST_PROB_MAP[catalyst_usage]
    
def amp_symbol_gen(current_amp, max_amp):
    """Generates a string of amp symbols based on current and max amps."""
    return '★' * current_amp + '☆' * (max_amp - current_amp)

CATALYST_COST_MAP = {
    "No Catalyst": 0,
    "Catalyst": st.session_state.get('catalyst_price', 100),
    "Stable Catalyst": st.session_state.get('catalyst_price', 100) * 2,
    "Potent Catalyst": st.session_state.get('potent_catalyst_price', 800),
    "3 Star Catalyst": st.session_state.get('potent_catalyst_price', 800) * 10,
    "4 Star Catalyst": st.session_state.get('potent_catalyst_price', 800) * 40
}

enhancement_level_select = st.selectbox(label="Enhancement Level", options=[f"{i}" for i in range(15,25)], index=st.session_state["enhancement_level"] - 15)
enhancement_level = int(enhancement_level_select)
st.session_state["enhancement_level"] = enhancement_level

### Calculate / Set Attempt Cost
st.markdown("Attempt Cost")
with st.expander(f"Calculate cost of each tap", expanded=True):
    gold_attempt_cost = st.number_input(label="Gold per tap", value=CONST.TAP_COST[enhancement_level])
    parts_attempt_cost = st.number_input(label="Cost of Spare Parts per tap", value=sum([i * j for i, j in zip(CONST.SPARE_PARTS_COST[enhancement_level], [100, 1500, 10000])]), help="The total cost of spare parts per tap. Please adjust to the current market value.")
    attempt_cost = gold_attempt_cost + parts_attempt_cost
    st.write(f"Total Cost Per 1-tap: `{attempt_cost:,.0f}` gold")

taps = st.session_state.get("glen_taps", 0)

total_gold_spent = st.session_state.get("glen_gold", 0)
failsafe = st.session_state.get("glen_failsafe", 0)

if not st.session_state.get("glen_amps"):
    st.session_state["glen_amps"] = st.session_state.get("glen_amps", [0] * CONST.AMP_THRESHOLDS[enhancement_level])
if not st.session_state.get("glen_current_amp"):
    st.session_state["glen_current_amp"] = st.session_state.get("glen_current_amp", 0)

amps = st.session_state["glen_amps"]
current_amp = st.session_state["glen_current_amp"]

catalyst_usage = st.selectbox(
    label="Catalyst Usage",
    options=["No Catalyst", "Catalyst", "Stable Catalyst", "Potent Catalyst"]
)

multi_until = st.selectbox(
    label="Multi until",
    options=[amp_symbol_gen(i+1, CONST.AMP_THRESHOLDS[enhancement_level]) for i in range(CONST.AMP_THRESHOLDS[enhancement_level])],
)
symbol_int_map = {amp_symbol_gen(i+1, CONST.AMP_THRESHOLDS[enhancement_level]): i + 1 for i in range(CONST.AMP_THRESHOLDS[enhancement_level])}



def enhance(gold, taps, catalysts, current_amp, all_amps, current_fs, complete=False, single=True):
    gold += attempt_cost
    taps += 1
    catalysts[catalyst_usage] = catalysts.get(catalyst_usage, 0) + 1
    current_amp = current_amp
    notif = []

    rng = np.random.random()
    if current_amp == len(amps):
        all_amps = [0] * CONST.AMP_THRESHOLDS[enhancement_level]
        current_amp = 0

        if current_fs == 6 or rng <= CONST.FAILSAFES[enhancement_level][current_fs]:
            complete = True
            return gold, taps, catalysts, current_amp, all_amps, current_fs, complete
        else:
            current_fs += 1
            notif.append({"error": "Oops. It's a Failsafe!"})
            return gold, taps, catalysts, current_amp, all_amps, current_fs, complete
    
    if all_amps[current_amp] == 6:
        all_amps[current_amp] = 0
        current_amp += 1
        if single:
            notif.append({"success": "Success! (it was pity though)" + f"`{amp_symbol_gen(current_amp - 1, CONST.AMP_THRESHOLDS[enhancement_level])}` -> `{amp_symbol_gen(current_amp, CONST.AMP_THRESHOLDS[enhancement_level])}`"})
    elif rng <= CONST.CATALYST_PROB_MAP[catalyst_usage]:
        all_amps[current_amp] = 0
        current_amp += 1
        if single:
            notif.append({"success": "Success! " + f"`{amp_symbol_gen(current_amp - 1, CONST.AMP_THRESHOLDS[enhancement_level])}` -> `{amp_symbol_gen(current_amp, CONST.AMP_THRESHOLDS[enhancement_level])}`"})
        logger.info(f"Success! {all_amps}, {current_amp}, {rng}")
    else:
        all_amps[current_amp] += 1
        current_amp = 0
        if single:
            notif.append({"error": "Failed. Try again!" + f"`{amp_symbol_gen(current_amp - 1, CONST.AMP_THRESHOLDS[enhancement_level])}` -> `{amp_symbol_gen(0, CONST.AMP_THRESHOLDS[enhancement_level])}`"})
        logger.info(f"Failed! {all_amps}, {current_amp}, {rng}" )
    
    return gold, taps, catalysts, current_amp, all_amps, current_fs, complete, notif

def reset():
    st.session_state["glen_taps"] = 0
    st.session_state["glen_gold"] = 0
    st.session_state["glen_failsafe"] = 0
    st.session_state['glen_catalysts'] = { "No Catalyst": 0, "Catalyst": 0, "Stable Catalyst": 0, "Potent Catalyst": 0 }
    st.session_state["glen_amps"] = [0] * CONST.AMP_THRESHOLDS[enhancement_level]
    st.session_state["glen_current_amp"] = 0
    st.session_state["notification"] = [{"info": "Resetting the enhancement state."}]


def enhance_buttons(gold, taps, catalysts, current_amp, all_amps, current_fs, catalyst_usage, multi_until, complete):
    col1, col2, col3 = st.columns([1, 2, 2])
    notifs = []

    def refresh():
        st.session_state["glen_gold"] = gold
        st.session_state["glen_taps"] = taps
        st.session_state['glen_catalysts'] = catalysts
        st.session_state["glen_current_amp"] = current_amp
        st.session_state["glen_amps"] = all_amps
        st.session_state["glen_failsafe"] = current_fs
        st.session_state["glen_complete"] = complete
        st.session_state["notification"] = notifs
        st.rerun()

    with col1:
        if not complete:
            if st.button(f"Enhance ({get_prob(enhancement_level, catalyst_usage, current_fs) * 100:,.0f}%)", type="primary", use_container_width=True):
                with st.spinner("Enhancing..."):
                    time.sleep(0.6)
                    gold, taps, catalysts, current_amp, all_amps, current_fs, complete, notifs = enhance(
                        gold, taps, catalysts, current_amp, all_amps, current_fs, complete,
                        single=True
                    )
                refresh()

    with col2:
        if not complete and current_amp != len(amps) and st.session_state["glen_current_amp"] < symbol_int_map[multi_until]:
            if st.button(f"Enhance 10x ({get_prob(enhancement_level, catalyst_usage, current_fs) * 100:,.0f}%)", type="primary", use_container_width=True):
                with st.spinner("Enhancing..."):
                    time.sleep(0.6)
                    for i, _ in enumerate(range(10)):
                        if current_amp == symbol_int_map[multi_until]:
                            notifs = [{"success": f"Reached the targetted amp after {i} steps.\nStopping multi-enhancement early.\n\nCurrent amp: `{amp_symbol_gen(current_amp, CONST.AMP_THRESHOLDS[enhancement_level])}`"}]
                            break

                        gold, taps, catalysts, current_amp, all_amps, current_fs, complete, notif = enhance(
                            gold, taps, catalysts, current_amp, all_amps, current_fs, complete,
                            single=False
                        )
                        notifs = [{"info": f"Enhanced `{i + 1}` times. Current amp: `{amp_symbol_gen(current_amp, CONST.AMP_THRESHOLDS[enhancement_level])}`"}] 
                refresh()


    with col3:
        if st.button("Reset", type="secondary", use_container_width=True):
            gold = 0
            taps = 0
            catalysts = { "No Catalyst": 0, "Catalyst": 0, "Stable Catalyst": 0, "Potent Catalyst": 0 }
            current_amp = 0
            all_amps = [0] * CONST.AMP_THRESHOLDS[enhancement_level]
            current_fs = 0
            complete = False
            refresh()
            


enhance_buttons(
    st.session_state["glen_gold"],
    st.session_state["glen_taps"],
    st.session_state['glen_catalysts'],
    st.session_state["glen_current_amp"],
    st.session_state["glen_amps"],
    st.session_state["glen_failsafe"],
    catalyst_usage,
    multi_until,
    st.session_state["glen_complete"]
)


if st.session_state["notification"]:
    for notif in st.session_state["notification"]:
        if "success" in notif:
            st.success(notif["success"])
        elif "error" in notif:
            st.error(notif["error"])
        elif "info" in notif:
            st.info(notif["info"])
        else:
            st.warning("Unknown notification type.")

total_cost = st.session_state['glen_gold'] / 1000000 * st.session_state['gold_price'] + \
    sum([CATALYST_COST_MAP[catalyst] * count for catalyst, count in st.session_state['glen_catalysts'].items()])

with st.container(border=True):
    st.write(f"Current Failsafe: `{st.session_state['glen_failsafe']}`")
    if st.session_state["glen_complete"]:
        # st.success(f"Congratulations! You have successfully enhanced from  +`{st.session_state['enhancement_level']}` to +`{st.session_state['enhancement_level'] + 1}`!")
        st.write(f"Total Opals Spent: `{total_cost:,.2f}`")
        st.stop()
    elif st.session_state['glen_current_amp'] == len(st.session_state['glen_amps']):  
        st.write(f"Current Amps: `{'★' * st.session_state['glen_current_amp']}`")
        # st.info("You have successfully reached max amplifications. Next attempt is a failsafe attempt.")
    else:
        st.write(f"Current Amps: `{'★' * st.session_state['glen_current_amp'] + '☆' * (CONST.AMP_THRESHOLDS[enhancement_level] -  st.session_state['glen_current_amp'])} -  {st.session_state['glen_amps'][st.session_state['glen_current_amp']]}/6`")
        with st.expander("Amp Status", expanded=False):
            st.write(f"Amp Status:")
            for i, amp in enumerate(st.session_state["glen_amps"] ):
                st.markdown(f"{'★' * i + '☆' * (len(amps) - i)} - {amp}/6")


with st.container(border=True):
    st.write(f"Total Cost: `{total_cost:,.2f}` opals")
    st.write(f"Total Taps: `{st.session_state['glen_taps']}` - (`{st.session_state['glen_gold'] :,.0f}` gold)")
    for catalyst, count in st.session_state['glen_catalysts'].items():
        if catalyst != "No Catalyst" and count > 0:
            st.write(f"{catalyst} - `{count:,.0f}`")



