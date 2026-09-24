import streamlit as st
from supabase import create_client, Client


def get_supabase() -> Client:
    """
    One Supabase client per Streamlit browser session.
    Do NOT use st.cache_resource for this client because the auth session is mutable.
    """
    if "supabase_client" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client
