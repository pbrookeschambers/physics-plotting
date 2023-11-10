import streamlit as st
import os


st.set_page_config(
    page_title="Plotting - LaTeX Cheat Sheet",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    # menu_items={
    #     "About": about
    # }
)



st.markdown("""<style>
    table {
        margin: auto;
        padding-block: 1em;
        margin-block: 1em;
    }
</style>""",
    unsafe_allow_html=True,)


st.markdown("""# $\LaTeX$ Cheat Sheet
            
This page gives a reference for many common $\LaTeX$ commands.""")

cols = st.columns(2)

sections = [
    f for f in os.listdir("pages/latex_sections") if f.endswith(".md")
]
# sort the sections alphabetically
sections = sorted(sections)
half = (len(sections) + 1)//2

for i, section in enumerate(sections):
    with open(f"pages/latex_sections/{section}") as f:
        name = section[3:-3]
        name = name.replace("_", " ").title()
        with cols[0] if i < half else cols[1]:
            with st.expander(name):
                st.markdown(f.read())