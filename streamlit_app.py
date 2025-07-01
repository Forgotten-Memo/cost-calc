import streamlit as st

st.set_page_config(
    page_title="CoA Enhancement Calculator",
    page_icon=":hammer:",
)

pages = {
    "Calculators": [
        st.Page("pages/whale.py", title="Whale Enhancement (+15 onwards)"),
        st.Page("pages/dolphin.py", title="Dolphin Enhancement (+15 Hell)"),
    ],
}

pg = st.navigation(pages, position="top")
pg.run()