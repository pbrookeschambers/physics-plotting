import json
from typing import List
import streamlit as st
import extra_streamlit_components as stx
from pathlib import Path
import base64
import time
import datetime
import logging

from data import DataSeries, FigureProperties

# @st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()
key_name = "physics_plotting_key"
data_dir = Path("data_cache")
if not data_dir.exists():
    data_dir.mkdir()

all_keys = [f.stem for f in data_dir.glob("*.json")]
all_cookies = None

def key_in_use(key):
    return key in all_keys

def get_all_cookies():
    global all_cookies
    if all_cookies is None:
        all_cookies = cookie_manager.get_all()
    return all_cookies
    # return cookie_manager.get_all()

def get_key():
    if key_name not in get_all_cookies():
        new_key = base64.b64encode(str(time.time()).encode("utf-8")).decode("utf-8")
        i = 10
        # incredibly unlikely that this will ever be true, but just in case
        while i > 0 and key_in_use(new_key):
            new_key = base64.b64encode(str(time.time()).encode("utf-8")).decode("utf-8")
            i -= 1
        if i == 0:
            raise Exception("Could not generate a unique key")
        # expires in 1 month
        cookie_manager.set(cookie = key_name, val = new_key)
        return new_key
    return cookie_manager.get(cookie = key_name)

def state_to_json(data_series, figure_properties):
    return {
        "time": str(datetime.datetime.now()),
        "data_series": [s.to_dict() for s in data_series],
        "figure_properties": figure_properties.to_dict(),
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
    return series, figure_properties

def save_data(key, data_series: List[DataSeries], figure_properties: FigureProperties):
    data = state_to_json(data_series, figure_properties)
    data_file = data_dir / f"{key}.json"
    json.dump(data, data_file.open("w"))


def clear_data(key):
    data_file = (data_dir / f"{key}.json")
    data_file.unlink()
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
        if time_since_last_edit(f.stem) > datetime.timedelta(days = 30):
            f.unlink()
        series, figure_properties = load_data(f.stem)
        if len(series) == 0:
            f.unlink()