import re
import streamlit as st
from utils.supabase_client import get_supabase


# ============================================================
# USERNAME VALIDATION
# ============================================================

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def normalize_username(username: str) -> str:
    return username.strip().lower()


def valid_username(username: str) -> bool:
    return bool(USERNAME_RE.fullmatch(username.strip()))


# ============================================================
# LOAD USER INTO SESSION
# ============================================================

def set_logged_in_user(auth_response) -> None:
    user = getattr(auth_response, "user", None)

    if user is None:
        raise ValueError(
            "Authentication succeeded but no user was returned."
        )

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

    st.session_state.user_email = (
        getattr(user, "email", "")
        or profile.get("email", "")
    )

    st.session_state.full_name = profile.get(
        "full_name",
        "Student",
    )

    st.session_state.username = profile.get(
        "username",
        "",
    )


# ============================================================
# SIGN UP
# ============================================================

def sign_up(
    full_name: str,
    username: str,
    email: str,
    password: str,
):
    supabase = get_supabase()

    return supabase.auth.sign_up(
        {
            "email": email.strip().lower(),
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name.strip(),
                    "username": normalize_username(username),
                }
            },
        }
    )


# ============================================================
# RESEND SIGNUP OTP
# ============================================================

def resend_signup_otp(email: str):
    supabase = get_supabase()

    return supabase.auth.resend(
        {
            "type": "signup",
            "email": email.strip().lower(),
        }
    )


# ============================================================
# VERIFY OTP
# ============================================================

def verify_signup_otp(
    email: str,
    token: str,
):
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


# ============================================================
# SIGN IN WITH USERNAME OR EMAIL
# ============================================================

def sign_in_with_username(
    username_or_email: str,
    password: str,
):
    supabase = get_supabase()

    identifier = username_or_email.strip().lower()

    if "@" in identifier:
        email = identifier

    else:
        lookup = supabase.rpc(
            "get_email_for_username",
            {
                "p_username":
                    normalize_username(identifier)
            },
        ).execute()

        email = lookup.data

        if not email:
            raise ValueError(
                "Username not found."
            )

    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    set_logged_in_user(response)

    return response


# ============================================================
# AUTH STATUS
# ============================================================

def is_logged_in() -> bool:
    return bool(
        st.session_state.get("user_id")
    )


# ============================================================
# PROTECT PRIVATE PAGES
# ============================================================

def require_auth():
    if not is_logged_in():
        st.warning(
            "Please sign in first."
        )

        st.stop()


# ============================================================
# LOGOUT
# ============================================================

def logout():
    try:
        get_supabase().auth.sign_out()

    except Exception:
        pass

    keys_to_clear = [
        "user_id",
        "user_email",
        "full_name",
        "username",
        "supabase_client",
        "gemini_client",
        "chat_messages",
        "generated_quiz",
        "generated_quiz_topic",
        "flashcards",
        "pending_verification_email",
        "verification_sent_at",
        "auth_view",
        "latest_study_plan",
        "selected_document_id",
    ]

    for key in keys_to_clear:
        st.session_state.pop(
            key,
            None,
        )


# ============================================================
# CUSTOM SIDEBAR
# ============================================================

def render_sidebar():

    st.markdown(
        """
        <style>

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    #181326 0%,
                    #211936 50%,
                    #171221 100%
                ) !important;

            border-right:
                1px solid
                rgba(
                    255,
                    255,
                    255,
                    0.07
                );
        }

        section[data-testid="stSidebar"]
        [data-testid="stSidebarUserContent"] {
            padding-top:
                1.25rem;
        }

        section[data-testid="stSidebar"] h2 {
            color:
                white !important;

            font-size:
                1.65rem !important;

            font-weight:
                850 !important;

            letter-spacing:
                -0.035em;
        }

        section[data-testid="stSidebar"] p {
            color:
                #BBB5CB;
        }

        section[data-testid="stSidebar"]
        [data-testid="stPageLink"] {
            border-radius:
                12px;

            margin-bottom:
                0.2rem;
        }

        section[data-testid="stSidebar"]
        [data-testid="stPageLink"] p {
            color:
                #F8FAFC !important;

            font-weight:
                560;
        }

        section[data-testid="stSidebar"]
        [data-testid="stPageLink"]:hover {
            background:
                rgba(
                    124,
                    58,
                    237,
                    0.18
                );
        }

        section[data-testid="stSidebar"] hr {
            border-color:
                rgba(
                    255,
                    255,
                    255,
                    0.12
                ) !important;
        }

        section[data-testid="stSidebar"]
        .stButton > button {
            min-height:
                44px;

            border-radius:
                12px;

            border:
                none;

            color:
                white;

            font-weight:
                700;

            background:
                linear-gradient(
                    135deg,
                    #7C3AED,
                    #4F46E5
                );
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:

        st.markdown(
            "## IntelliLearn"
        )

        full_name = (
            st.session_state.get(
                "full_name",
                "",
            )
        )

        username = (
            st.session_state.get(
                "username",
                "student",
            )
        )

        if full_name:
            st.caption(
                f"Welcome, **{full_name}**"
            )

        st.caption(
            f"Signed in as **{username}**"
        )

        st.divider()

        st.page_link(
            "pages/1_Dashboard.py",
            label="Dashboard",
            icon=":material/dashboard:",
        )

        st.page_link(
            "pages/2_My_Documents.py",
            label="My Documents",
            icon=":material/folder:",
        )

        st.page_link(
            "pages/3_Ask_IntelliLearn.py",
            label="Ask IntelliLearn",
            icon=":material/smart_toy:",
        )

        st.page_link(
            "pages/4_Quiz.py",
            label="Quiz",
            icon=":material/quiz:",
        )

        st.page_link(
            "pages/5_Flashcards.py",
            label="Flashcards",
            icon=":material/style:",
        )

        st.page_link(
            "pages/6_Study_Plan.py",
            label="Study Plan",
            icon=":material/calendar_month:",
        )

        st.page_link(
            "pages/7_Progress.py",
            label="Progress",
            icon=":material/monitoring:",
        )

        st.divider()

        if st.button(
            "Sign out",
            use_container_width=True,
        ):
            logout()
            st.rerun()
