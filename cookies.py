# import streamlit as st
# from streamlit.runtime.scriptrunner import get_script_run_ctx
# from streamlit.components.v1 import html
import logging

# cookies = None

# def update_cookies_list():
#     global cookies
#     ctx = get_script_run_ctx()
#     server = st.runtime.get_instance().get_client(ctx.session_id)
#     cookies = server.cookies
#     logging.info(f"Updated cookies list")
#     for key, val in cookies.items():
#         logging.info(f"    {key}: {val.value}")

# def get_all_cookies() -> dict:
#     global cookies
#     return {c.name: c.value for c in cookies}

# def get_cookie(name: str) -> str:
#     global cookies
#     if name in cookies:
#         return cookies[name].value
#     return None

# def set_cookie(name: str, value: str, expires_in: int = 3600):
#     html(f"""
# <script>
#     document.cookie = "{name}={value}; path=/; max-age={expires_in}";
# </script>
# """, height=0)

# def has_cookie(name: str) -> bool:
#     global cookies
#     return name in cookies

# def delete_cookie(name: str):
#     html(f"""
# <script>
#     document.cookie = "{name}=; path=/; max-age=0";
# </script>
# """, height=0)

from cookie_component import cookie_component

def get_all_cookies() -> dict:
    response = cookie_component(mode = "get_all_cookies")
    # default return value is an empty string. First run will always be empty
    if response == "" or response is None or not response["success"]:
        logging.info("Update cookies list. No cookies found")
        return {}
    cookies = response["response"]
    cookies_dict = {}
    for cookie in cookies:
        cookies_dict[cookie["name"]] = cookie["value"]
    logging.info("Update cookies list. Found cookies:")
    for key, val in cookies_dict.items():
        logging.info(f"    {key}: {val}")
    if len(cookies_dict) == 0:
        logging.info("    None")
    return cookies_dict

def get_cookie(name: str) -> str:
    response = cookie_component("get_cookie", name=name)
    if response == "" or response is None or not response["success"]:
        return None
    return response["response"]

def set_cookie(name: str, value: str, expires_in: int = 30):
    # expires_in is in days
    response = cookie_component("set_cookie", name=name, value=value, expires_in_days=expires_in)
    if response == "" or response is None or not response["success"]:
        return False
    return True

def has_cookie(name: str) -> bool:
    cookies = get_all_cookies()
    return name in cookies

def delete_cookie(name: str):
    response = cookie_component("delete_cookie", name=name)
    if response == "" or response is None or not response["success"]:
        return False
    return True
