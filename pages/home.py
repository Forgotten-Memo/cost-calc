import streamlit as st

def render_page():
    st.title("CoA Utilities")

    st.markdown(
        """
        <div style="border:1px solid #ddd; border-radius:6px; padding:16px;">
            A collection of utilities for CoA. By シHyacine (IW01) AKA Mem0.
        </div>
        <br/>
        """,
        unsafe_allow_html=True
    )

    st.subheader("📢 Recent Updates")
    updates = [
        {"title": "2025-10-02 - v0.2.1", "message": "- Added home page and notice board for recent updates\n"
        "- Luck Calc: Update weights and probabilities to account for hidden rates at 4/6 and 5/6. This moderates luck scores significantly.\n"
        "- Luck Calc: Add ability to specify redundant taps and level that use guaranteed amp catalysts.\n"
        "- Optimiser: Add ability to specify current failsafe, amp, pity.\n"
        "- Style change to be more appealing to eyes."},
    ]

    for update in updates:
        with st.expander(update['title'], expanded=True):
            st.markdown(f"{update['message']}", unsafe_allow_html=True)


    st.subheader("🔗 Utilities")
    pages = [
        {"name": "Optimiser 💰", "url": "/optimiser"},
        {"name": "Simulator 🎰", "url": "/simulator"},
        {"name": "Luck Calculator 🍀", "url": "/luck"},
        {"name": "Damage Forecast 📈", "url": "/dmg"},
    ]


    cols = st.columns(3)
    for i, page in enumerate(pages):
        with cols[i%3].container(border=True):
            st.markdown(f"### [{page['name']}]({page['url']})")
            if page['name'] == "Optimiser 💰":
                st.write(
                    "Calculate the cost of enhancing your gear based on current market prices.")
            elif page['name'] == "Simulator 🎰":
                st.write(
                    "Simulate enhancement attempts to see potential outcomes and costs."
                )
            elif page['name'] == "Luck Calculator 🍀":
                st.write(
                    "Estimate your luck score based on your current enhancement levels and total taps.")
            elif page['name'] == "Damage Forecast 📈":
                st.write(
                    "Predict abyssal frontier damage for different classes based on your battle power. (Early access)")

render_page()