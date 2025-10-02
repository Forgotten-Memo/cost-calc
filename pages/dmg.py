import streamlit as st
import joblib
import pandas as pd
import constants as CONST
from utils.graphing import plot_class_trendlines_px

@st.cache_resource
def load_pipeline():
    try:
        return joblib.load('./static/abyss_model_0.1.pkl')
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None
    
st.title("Abyssal Frontier DMG Forecast")
with st.container(border=True):
    st.write("A tool to predict abyssal frontier dmg for different classes based on your power level. "
            "You can compare to the baseline scores to gauge whether you are performing above or below average for your power level. " 
            "By シHyacine (IW01) @forgotten_memo.")
    st.info("This is an early release and the model is currently trained on limited data. "
            "As such, accuracy may not be ideal yet. "
            "To expand the feature set (such as accounting for more variables) and to improve accuracy, more data is required. "
            "If you would like to volunteer to help collect data, please contact @forgotten_memo on Discord or help submit abyssal frontier data directly to https://forms.gle/Xgt39GmyDoRU6sSf7. ")

pipeline = load_pipeline()

if pipeline:
    tabs = st.tabs(["Predict", "Compare"])
    with tabs[0]:
        with st.container(border=True):
            st.subheader("Configuration")
            cols = st.columns(2)
            with cols[0]:
                bp = st.number_input(label="Battle Power", min_value=1000, max_value=200000, value=80000, step=1000, help="Your current battle power")
            with cols[1]:
                char_class = st.selectbox(label="Class", options=CONST.CLASSES, help="Your character class. Spectre and Mirage are not added yet due to insufficient data.")
            
            with st.expander("Additional Variables (Future Release)", expanded=False):
                sub_vars = st.columns(4)
                with sub_vars[0]:
                    armor_set = st.selectbox(label="Armor Set", options=["Unknown", "Lv 60 Destiny", "Chariot", "Calvary", "Unforgiving"], index=0, help="Your armor set", disabled=True)
                with sub_vars[1]:
                    accessory_set = st.selectbox(label="Accessory Set", options=["Unknown", "Lv 60 Destiny"], index=0, help="Your accessory set", disabled=True)
                with sub_vars[2]:
                    queen_weapon = st.checkbox(label="Queen Weapon", value=False, help="Whether you are using the Queen's weapon", disabled=True)
                with sub_vars[3]:
                    max_buffs = st.checkbox(label="Use Buffs", value=True, help="Whether you are using max-buffs (potion, food, drink)", disabled=True)
            
        if st.button("Predict DMG"):
            if pipeline:
                result = pipeline.predict(pd.DataFrame([{'bp': bp, 'class': char_class}]))
                st.success(f"Expected DMG: {result[0]:,.2f}")
            else:
                st.error("Model not loaded correctly.")

    with tabs[1]:
        selected_classes = st.multiselect(
            label="Select up to 4 classes to compare",
            options=CONST.CLASSES,
            default=["Gunner", "Cloudstrider"],
            max_selections=4,
            help="Choose up to 4 classes to compare their predicted DMG."
        )
        if st.button("Generate Comparison Plot"):
            if selected_classes:
                fig = plot_class_trendlines_px(selected_classes, pipeline, bp_min=55000, bp_max_plot=110000, n_points=100, std_scale=1)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Please select at least one class to compare.")
