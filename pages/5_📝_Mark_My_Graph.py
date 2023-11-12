
import streamlit as st

from marking import check_for_problems
from persistance import get_key, load_data


st.set_page_config(
    page_title="Plotting - Mark My Graph",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    key = get_key()
    _data_series, _figure_properties, _csv_file = load_data(key)
    st.session_state.data_series = _data_series
    st.session_state.figure_properties = _figure_properties
    st.session_state.csv_file = _csv_file
    st.session_state.should_load = False
except Exception as e:
    pass

st.title("Mark My Graph")
if "data_series" in st.session_state and len(st.session_state.data_series) > 0:
    check_for_problems()
else:
    st.markdown("It looks like you don't have an active figure. Go to the [Home page](/) to create one, or the [Help page](/Help) for guidance on how to use this app.")