import streamlit as st

st.set_page_config(
    page_title="CoA Enhancement Calculator",
    page_icon=":hammer:",
)
st.set_page_config(layout="wide")

st.session_state.setdefault('gold_price', 130.0)

pages = {
    "Tools": [
        st.Page("pages/home.py", title="Home"),
        st.Page("pages/optimiser.py", title="Enhancement Optimiser"),
        st.Page("pages/simulator.py", title="Enhancement Simulator"),
        st.Page("pages/luck.py", title="Luck Scorer"),
        st.Page("pages/dmg.py", title="Abyssal Frontier DMG Forecast (EA)"),
        st.Page("pages/dolphin.py", title="<+15 Enhancement (DEP)"),
        st.Page("pages/glen.py", title="Glen Casino (DEP)"),
        
    ],
}

pg = st.navigation(pages, position="top")
st.sidebar.title("Settings")
st.session_state['gold_price'] = st.sidebar.number_input("Gold Market Price (Per 1M)", value=130.0)
st.session_state['catalyst_price'] = st.sidebar.number_input("Catalyst Value (Opals)", value=100, help="The value you assign to a catalyst (e.g. lower if you often buy them discounted)")
st.session_state['potent_catalyst_price'] = st.sidebar.number_input("Potent Catalyst Value (Opals)", value=800, help="The value you assign to a potent catalyst (e.g. lower if you often buy them discounted)")


pg.run()