import json
from typing import List
import numpy as np
import streamlit as st
from pathlib import Path
import base64
import time
import datetime
import logging

from data import CSVFile, DataSeries, FigureProperties
from cookies import (
    get_cookie,
    has_cookie,
    set_cookie,
    delete_cookie,
    update_cookies_list,
)

key_name = "physics_plotting_key"
data_dir = Path("data_cache")
if not data_dir.exists():
    data_dir.mkdir()

all_keys = [f.stem for f in data_dir.glob("*.json")]
all_cookies = None


def key_in_use(key):
    return key in all_keys


def generate_uuid() -> str:
    d = datetime.datetime.now()
    # convert d to int
    d = int(d.timestamp())
    d2 = int(time.perf_counter_ns())
    uuid = ""
    for c in range(32):
        r = np.random.randint(0, 16)
        if d > 0:
            r = (d + r) % 16
            d = d // 16
        else:
            r = (d2 + r) % 16
            d2 = d2 // 16
        uuid += hex(r)[2:]
    return uuid


#### The library that this used, extra-streamlit-components, shared cookies between ALL sessions on the same server. This was... causing problems.
# def get_key():
#     if not "cookie_key" in st.session_state and st.session_state.cookie_key is None and
#         new_key = generate_uuid()
#         i = 10
#         # incredibly unlikely that this will ever be true, but just in case
#         while i > 0 and key_in_use(new_key):
#             new_key = generate_uuid()
#             i -= 1
#         if i == 0:
#             raise Exception("Could not generate a unique key")
#         # expires in 1 month
#         cookie_manager.set(cookie = key_name, val = new_key)
#         logging.info(f"Generated new key: {new_key}")
#         return new_key
#     logging.info(f"Using existing key: {cookie_manager.get(cookie = key_name)}")
#     return cookie_manager.get(cookie = key_name)


def get_key():
    update_cookies_list()
    # is there a key in the session state? If so, return that
    if "cookie_key" in st.session_state and st.session_state.cookie_key is not None:
        return st.session_state.cookie_key
    # Is there a key in the browser cookies? If so, return that
    if has_cookie(key_name):
        return get_cookie(key_name)

    # generate a new key
    new_key = generate_uuid()
    i = 10
    # incredibly unlikely that this will ever be true, but just in case
    while i > 0 and key_in_use(new_key):
        new_key = generate_uuid()
        i -= 1
    if i == 0:
        raise Exception("Could not generate a unique key")
    # expires in 1 month
    set_cookie(key_name, new_key, expires_in=2592000)
    logging.info(f"Generated new key: {new_key}")
    # add the key to the session state
    st.session_state.cookie_key = new_key
    return new_key


def state_to_json(data_series, figure_properties, csv_file=None):
    return {
        "time": str(datetime.datetime.now()),
        "data_series": [s.to_dict() for s in data_series],
        "figure_properties": figure_properties.to_dict(),
        "csv_file": None if csv_file is None else csv_file.to_dict(),
    }


def load_data(key):
    data_file = data_dir / f"{key}.json"
    if not data_file.exists():
        # create it as an empty json file

        data = state_to_json([], FigureProperties.default())
        # json.dump(data, data_file.open("w"))
    else:
        data = json.load(data_file.open())
    series = [DataSeries.from_dict(d) for d in data["data_series"]]
    figure_properties = FigureProperties.from_dict(data["figure_properties"])
    csv_file = (
        None
        if ("csv_file" not in data or data["csv_file"] is None)
        else CSVFile.from_dict(data["csv_file"])
    )
    return series, figure_properties, csv_file


def save_data(
    key,
    data_series: List[DataSeries],
    figure_properties: FigureProperties,
    csv_file=None,
):
    data = state_to_json(data_series, figure_properties, csv_file)
    data_file = data_dir / f"{key}.json"
    json.dump(data, data_file.open("w"))


def clear_data(key):
    data_file = data_dir / f"{key}.json"
    try:
        data_file.unlink()
    except FileNotFoundError:
        logging.warning(f"Could not find file {data_file} when clearing data")
    # create the empty file again
    data = state_to_json([], FigureProperties.default())
    json.dump(data, data_file.open("w"))
    st.session_state.should_load = True


def time_since_last_edit(key):
    data_file = data_dir / f"{key}.json"
    if not data_file.exists():
        return None
    data = json.load(data_file.open())
    t = datetime.datetime.strptime(data["time"], "%Y-%m-%d %H:%M:%S.%f")
    return datetime.datetime.now() - t


def clean_old_files():
    for f in data_dir.glob("*.json"):
        if time_since_last_edit(f.stem) > datetime.timedelta(days=30):
            f.unlink()
        series, figure_properties, csv_file = load_data(f.stem)
        if len(series) == 0:
            f.unlink()
