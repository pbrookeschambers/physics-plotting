
import streamlit as st

from marking import check_for_problems
from persistence import get_existing_key, get_new_key, load_data
import logging


st.set_page_config(
    page_title="Plotting - Mark My Graph",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    default_attempts = 3

    if "attempt" not in st.session_state:
        st.session_state.attempt = default_attempts # will attempt to find cookies this many times, resetting each time cookies are found.

    if "cookie_key" in st.session_state and st.session_state.cookie_key is not None:
        logging.info(f"Using existing key (from state -- home): {st.session_state.cookie_key}")
        key = st.session_state.cookie_key
    else:
        key = get_existing_key()
        if key is None:
            if st.session_state.attempt > 1:
                st.session_state.attempt -= 1
            else:
                key = get_new_key()
                st.session_state.cookie_key = key
        else:
            st.session_state.should_load = True
            st.session_state.attempt = default_attempts
            st.session_state.cookie_key = key
    
    if not "should_load" in st.session_state:
        st.session_state.should_load = True
    if st.session_state.should_load:
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