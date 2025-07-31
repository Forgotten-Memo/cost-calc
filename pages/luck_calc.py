import streamlit as st
from scipy.stats import norm
import constants as CONST 
import utils
import logging

st.title("Luck Scorer")
st.info("A fun scorer that gauges how lucky you are based on your total number of taps and enhancement levels. Thresholds are quite arbitrary for now and this is just for fun.\n\n"\
        "To find your total taps, go to character icon > click manual on bottom left > go to life > look at enhancement section\n\n"\
        "This is an early release that is only intended for used by those with resonance > 165 and does not account for failsafes or current amp progress.")
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

total_taps = st.number_input("Total Taps", 0, 10000000, 1800, help="The total number of taps you have made in the game. This is used to calculate your luck score.")

with st.expander("Enhancement Levels", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        weapon = st.number_input("Weapon Enhancement Level", 0, 25, 18)
        helmet = st.number_input("Helmet Enhancement Level", 0, 25, 15)
        breastplate = st.number_input("Breastplate Enhancement Level", 0, 25, 15)
        gauntlets = st.number_input("Gauntlets Enhancement Level", 0, 25, 15)
        pants = st.number_input("Pants Enhancement Level", 0, 25, 15)
        boots = st.number_input("Boots Enhancement Level", 0, 25, 15)

    with col2:
        necklace = st.number_input("Necklace Enhancement Level", 0, 25, 15)
        bracers = st.number_input("Bracers Enhancement Level", 0, 25, 15)
        ring = st.number_input("Ring Enhancement Level", 0, 25, 15)
        talisman = st.number_input("Talisman Enhancement Level", 0, 25, 15)
        seal = st.number_input("Seal Enhancement Level", 0, 25, 15)

total_resonance = sum([
    weapon, helmet, breastplate, gauntlets, pants, boots,
    necklace, bracers, ring, talisman, seal
])

expectation_map = {i: 0 for i in range(1, 11)}
expectation_map[11] = 5
expectation_map[12] = 20
expectation_map[13] = 25
expectation_map[14] = 40
expectation_map[15] = 105
for i in range(16, 26):
    expectation_map[i] = 3.9 ** (CONST.AMP_THRESHOLDS[i-1]) / utils.cumulative_prob(utils.modified_prob(CONST.FAILSAFES[i-1], lambda x: x + 0.07)) + expectation_map[i-1]

expected_taps = sum(expectation_map[i] for i in [weapon, helmet, breastplate, gauntlets, pants, boots,
    necklace, bracers, ring, talisman, seal])
stdev = sum((expectation_map[i] / 1.5) ** 2 for i in [weapon, helmet, breastplate, gauntlets, pants, boots,
    necklace, bracers, ring, talisman, seal]) ** 0.5

percentile = norm.cdf(total_taps, loc=expected_taps, scale=stdev)

luck_status = "Very Unlucky"
luck_thresholds = {
    "Very Lucky": 0.90,
    "Lucky": 0.75,
    "Neutral": 0.25,
    "Unlucky": 0.10,
}

with st.container(border=True):
    st.write(f"Total Taps: `{total_taps:,.0f}` (Resonance: `{total_resonance}`)")
    st.write(f"Baseline Taps: `{expected_taps:,.0f}`")

     
    for label, threshold in luck_thresholds.items():
        if 1 - percentile >= threshold:
            luck_status = label
            break

    st.write(f"Luck Score: `{1-percentile:.3f}` (`{luck_status}`)")

