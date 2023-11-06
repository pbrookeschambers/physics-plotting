import streamlit as st
import os


st.set_page_config(
    page_title="Plotting - Help",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    # menu_items={
    #     "About": about
    # }
)

st.markdown("""# Plotting Help
            
This app is designed to help you create well-formatted plots. It was created by Peter Brookes Chambers (p.brookes-chambers1@newcastle.ac.uk) using Streamlit.
         
This page is designed to help you get started with the app and create plots. For a more technical description of the app, please see the Docs page.""")

col1, col2 = st.columns(2)

sections = [f for f in os.listdir("pages/help_sections") if f.endswith(".md")]
# sort the sections alphabetically
sections = sorted(sections)
half = (len(sections) + 1)//2

for i, section in enumerate(sections):
    with open(f"pages/help_sections/{section}") as f:
        name = section[3:-3]
        name = name.replace("_", " ").title()
        with col1 if i < half else col2:
            with st.expander(name):
                st.markdown(f.read())