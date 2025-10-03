import streamlit as st
from scipy.stats import norm
import constants as CONST 
import utils.utils as utils
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CUMULATIVE_AMP_EXP = 3.75
CATALYST_MOD = 0.04
DEFAULT_TAPS = 1650
DEFAULT_WEAP_LEVEL = 18
DEFAULT_ARMOR_LEVEL = 15

st.title("Luck Scorer")
description = "A fun scorer that gauges how lucky you are based on your total number of taps and enhancement levels. Thresholds are quite arbitrary for now and this is just for fun.\n"\
        "- To find your total taps, go to character icon > click manual on bottom left > go to life > look at enhancement section.\n"\
        "- This is an early release that is only intended for used by those with resonance > 165 and does not account for failsafes or current amp progress.\n"\
        "- If you performed actions that may inflate or deflate tap count (e.g. white gear tap / guaranteed amp catalyst usage), you may specify them to moderate the calculated taps and obtain a more accurate result."\
        "- Assumes conservative catalyst usage."

with st.container(border=True):
    st.markdown(description)


### Display Main Inputs
total_taps = st.number_input("Total Taps", 0, 10000000, DEFAULT_TAPS, help="The total number of taps you have made in the game. This is used to calculate your luck score.")

with st.expander("Enhancement Levels", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        weapon = st.number_input("Weapon Enhancement Level", 0, 25, DEFAULT_WEAP_LEVEL)
        helmet = st.number_input("Helmet Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        breastplate = st.number_input("Breastplate Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        gauntlets = st.number_input("Gauntlets Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        pants = st.number_input("Pants Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        boots = st.number_input("Boots Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)

    with col2:
        necklace = st.number_input("Necklace Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        bracers = st.number_input("Bracers Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        ring = st.number_input("Ring Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        talisman = st.number_input("Talisman Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)
        seal = st.number_input("Seal Enhancement Level", 0, 25, DEFAULT_ARMOR_LEVEL)

total_resonance = sum([
    weapon, helmet, breastplate, gauntlets, pants, boots,
    necklace, bracers, ring, talisman, seal
])

### Hard code expectation map for levels 1-15
expectation_map = {i: 0 for i in range(1, 11)}
expectation_map[11] = 5
expectation_map[12] = 20
expectation_map[13] = 25
expectation_map[14] = 40
expectation_map[15] = 105


### Calculate expectation for levels 16-25 using heuristics
# """
# Logic:
# - At higher levels, more catalysts will be used, which reduces the expected taps.
# """

for i in range(16, 26):
    expectation_map[i] = (CUMULATIVE_AMP_EXP + min((20-i) * CATALYST_MOD, 0)) ** (CONST.AMP_THRESHOLDS[i-1]) / utils.cumulative_prob(utils.modified_prob(CONST.FAILSAFES[i-1], lambda x: min(x + 0.07, 1.00))) + expectation_map[i-1]


### Display Tap Modifiers
with st.expander("Tap Modifiers (Optional)", expanded=False):
    mod_cols = st.columns(3)
    three_star_catalyst_used = mod_cols[0].number_input(
        "Number of 3-star catalyst used", 0, 100,
        help="Number of 3-star catalysts used. e.g. if used `2x` for helmet lv 16 and `2x` for 17 and `1x` for weapon lv 17-> put `5`. This will reduce the expected taps."
    )
    four_star_catalyst_used = mod_cols[1].number_input(
        "Number of 4-star catalyst used", 0, 100,
        help="Number of 4-star catalysts used. e.g. if used `2x` for helmet lv 19 and `2x` 20 and `1x` for weapon lv 20 -> put `5`. This will reduce the expected taps."
    )
    redundant_gear_taps = mod_cols[2].number_input(
        "Redundant Gear Taps", 0, 1000000, 0,
        help="Number of taps spent on redundant gear (i.e. white gear taps). This will be subtracted from your total taps for a more accurate luck score."
    )

### Calculate tap modifications
adjusted_total_taps = max(0, total_taps - redundant_gear_taps)
reduced_taps = (CUMULATIVE_AMP_EXP ** 3 - CUMULATIVE_AMP_EXP ** 2) * three_star_catalyst_used + \
    (CUMULATIVE_AMP_EXP ** 4 - CUMULATIVE_AMP_EXP ** 3) * four_star_catalyst_used
expected_taps = sum(expectation_map[i] for i in [weapon, helmet, breastplate, gauntlets, pants, boots,
    necklace, bracers, ring, talisman, seal])

### Calculate Stats and Results
stdev = sum((expectation_map[i] * 0.5) ** 2 for i in [weapon, helmet, breastplate, gauntlets, pants, boots,
    necklace, bracers, ring, talisman, seal]) ** 0.5
percentile = norm.cdf(adjusted_total_taps, loc=expected_taps-reduced_taps, scale=stdev)

luck_status = "Victim of Glen"
luck_thresholds = {
    "RNGesus": 0.95,
    "Very Lucky": 0.85,
    "Lucky": 0.65,
    "Neutral": 0.35,
    "Unlucky": 0.15,
    "Victim of Glen": 0.05
}


### Display results
with st.container(border=True):
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("Results")
        st.write(f"**Total Counted Taps:** `{total_taps:,.0f} - {redundant_gear_taps:,.0f} = {total_taps - redundant_gear_taps:,.0f}` (Resonance: `{total_resonance}`)")
        st.write(f"**Expected Taps:** `{expected_taps:,.0f} - {reduced_taps:,.0f} = {expected_taps - reduced_taps:,.0f}`")

        for label, threshold in luck_thresholds.items():
            if 1 - percentile >= threshold:
                luck_status = label
                break

        st.write(f"**Luck Score:** `{1-percentile:.3f}` (`{luck_status}`)")

    with right_col:
        st.subheader("Legend")
        st.markdown("""
        - `RNGesus`: > 0.95
        - `Very Lucky`: 0.85-0.95
        - `Lucky`: 0.65-0.85
        - `Neutral`: 0.35-0.65
        - `Unlucky`: 0.15-0.35
        - `Very Unlucky`:  0.05-0.15
        - `Victim of Glen`: < 0.05
        """)



