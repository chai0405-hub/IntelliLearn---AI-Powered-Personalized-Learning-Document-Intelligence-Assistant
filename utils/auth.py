import re
import streamlit as st
from utils.supabase_client import get_supabase


USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def normalize_username(username: str) -> str:
    return username.strip().lower()


def valid_username(username: str) -> bool:
    return bool(USERNAME_RE.fullmatch(username.strip()))


def set_logged_in_user(auth_response) -> None:
    user = getattr(auth_response, "user", None)
    if user is None:
        raise ValueError("Authentication succeeded but no user was returned.")

    supabase = get_supabase()
    profile_response = (
        supabase.table("profiles")
        .select("id, full_name, username, email")
        .eq("id", str(user.id))
        .maybe_single()
        .execute()
    )
    profile = profile_response.data or {}

    st.session_state.user_id = str(user.id)
    st.session_state.user_email = getattr(user, "email", "") or profile.get("email", "")
    st.session_state.full_name = profile.get("full_name", "Student")
    st.session_state.username = profile.get("username", "")


def sign_up(full_name: str, username: str, email: str, password: str):
    supabase = get_supabase()
    username = normalize_username(username)

    return supabase.auth.sign_up(
        {
            "email": email.strip().lower(),
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name.strip(),
                    "username": username,
                }
            },
        }
    )


def verify_signup_otp(email: str, token: str):
    supabase = get_supabase()
    response = supabase.auth.verify_otp(
        {
            "email": email.strip().lower(),
            "token": token.strip(),
            "type": "email",
        }
    )
    if getattr(response, "user", None):
        set_logged_in_user(response)
    return response


def sign_in_with_username(username_or_email: str, password: str):
    supabase = get_supabase()
    identifier = username_or_email.strip().lower()

    if "@" in identifier:
        email = identifier
    else:
        lookup = supabase.rpc(
            "get_email_for_username",
            {"p_username": normalize_username(identifier)},
        ).execute()

        email = lookup.data
        if not email:
            raise ValueError("Username not found.")

    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )
    set_logged_in_user(response)
    return response


def is_logged_in() -> bool:
    return bool(st.session_state.get("user_id"))


def require_auth():
    if not is_logged_in():
        st.warning("Please sign in first.")
        if st.button("Go to Login"):
            st.switch_page("app.py")
        st.stop()


def logout():
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass

    for key in [
        "user_id",
        "user_email",
        "full_name",
        "username",
        "supabase_client",
        "chat_messages",
        "generated_quiz",
        "flashcards",
    ]:
        st.session_state.pop(key, None)


def render_sidebar():
    with st.sidebar:
        st.markdown("## IntelliLearn")
        if is_logged_in():
            st.caption(f"Signed in as **{st.session_state.get('username', 'student')}**")
            st.page_link("pages/1_Dashboard.py", label="Dashboard")
            st.page_link("pages/2_My_Documents.py", label="My Documents")
            st.page_link("pages/3_Ask_IntelliLearn.py", label="Ask IntelliLearn")
            st.page_link("pages/4_Quiz.py", label="Quiz")
            st.page_link("pages/5_Flashcards.py", label="Flashcards")
            st.page_link("pages/6_Study_Plan.py", label="Study Plan")
            st.page_link("pages/7_Progress.py", label="Progress")
            st.divider()
            if st.button("Sign out", use_container_width=True):
                logout()
                st.switch_page("app.py")
