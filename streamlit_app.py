import streamlit as st

st.set_page_config(
    page_title="CoA Enhancement Calculator",
    page_icon=":hammer:",
)

st.session_state.setdefault('gold_price', 190.0)

pages = {
    "Calculators": [
        st.Page("pages/whale.py", title="Whale Enhancement (+15 onwards)"),
        st.Page("pages/dolphin.py", title="Dolphin Enhancement (+15 Hell)"),
        st.Page("pages/glen.py", title="Glen Casino (BETA)"),
        st.Page("pages/luck_calc.py", title="Luck Scorer (BETA)"),
    ],
}

pg = st.navigation(pages, position="top")

st.session_state['gold_price'] = st.sidebar.number_input("Gold Market Price (Per 1M)", value=180.0)
st.session_state['catalyst_price'] = st.sidebar.number_input("Catalyst Value (Opals)", value=100, help="The value you assign to a catalyst (e.g. lower if you often buy them discounted)")
st.session_state['potent_catalyst_price'] = st.sidebar.number_input("Potent Catalyst Value (Opals)", value=800, help="The value you assign to a potent catalyst (e.g. lower if you often buy them discounted)")


pg.run()