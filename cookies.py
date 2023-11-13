import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.components.v1 import html

cookies = None

def update_cookies_list():
    global cookies
    ctx = get_script_run_ctx()
    server = st.runtime.get_instance().get_client(ctx.session_id)
    cookies = server.cookies

def get_all_cookies() -> dict:
    global cookies
    return {c.name: c.value for c in cookies}

def get_cookie(name: str) -> str:
    global cookies
    if name in cookies:
        return cookies[name].value
    return None

def set_cookie(name: str, value: str, expires_in: int = 3600):
    html(f"""
<script>
    document.cookie = "{name}={value}; path=/; max-age={expires_in}";
</script>
""", height=0)

def has_cookie(name: str) -> bool:
    global cookies
    return name in cookies

def delete_cookie(name: str):
    html(f"""
<script>
    document.cookie = "{name}=; path=/; max-age=0";
</script>
""", height=0)