import logging
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

cols = st.columns(3)

# sections = [f for f in os.listdir("pages/help_sections") if f.endswith(".md")]
# # sort the sections alphabetically
# sections = sorted(sections)
# items_per_col = (len(sections) + len(cols) - 1) // len(cols)

# for i, section in enumerate(sections):
#     with open(f"pages/help_sections/{section}") as f:
#         name = section[3:-3]
#         name = name.replace("_", " ").title()
#         with cols[i // items_per_col]:
#             with st.expander(f":blue[{name}]" ):
#                 st.markdown(f.read())

# sections = [d for d in os.listdir("pages/help_sections") if os.path.isdir(os.path.join("pages/help_sections", d))]
# # sort the sections alphabetically
# sections = sorted(sections)
# topics = []
# section_indices = []
# for section in sections:
#     section_indices.append(len(topics))
#     ts = [f for f in os.listdir(os.path.join("pages/help_sections", section)) if f.endswith(".md")]
#     ts = sorted(ts)
#     for t in ts:
#         topics.append(t)

# items_per_col = (len(topics) + len(cols) - 1) // len(cols)
# for i, topic in enumerate(topics):
#     col_idx = i // items_per_col
#     if i in section_indices:
#         section = sections[section_indices.index(i)]
#         name = section[3:].replace("_", " ").title()
#         with cols[col_idx]:
#             st.subheader(name)
#     with cols[col_idx]:
#         with st.expander(topic[3:-3].replace("_", " ").title()):
#             with open(os.path.join("pages/help_sections", section, topic)) as f:
#                 st.markdown(f.read())

sections = [d for d in os.listdir("pages/help_sections") if os.path.isdir(os.path.join("pages/help_sections", d))]
sections = sorted(sections)
logging.info(sections)

def add_section(section_dir):
    name = section_dir[3:].replace("_", " ").title()
    st.subheader(name)
    files = [f for f in os.listdir(os.path.join("pages/help_sections", section_dir)) if f.endswith(".md")]
    files = sorted(files)
    logging.info(files)
    for f in files:
        with st.expander(f[3:-3].replace("_", " ").title()):
            with open(os.path.join("pages/help_sections", section_dir, f)) as f:
                st.markdown(f.read())

with cols[0]:
    add_section(sections[0])
    add_section(sections[1])
with cols[1]:
    add_section(sections[2])
with cols[2]:
    add_section(sections[3])