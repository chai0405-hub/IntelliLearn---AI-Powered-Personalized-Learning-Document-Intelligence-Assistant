import streamlit as st
from utils.auth import (
    is_logged_in,
    sign_in_with_username,
    sign_up,
    verify_signup_otp,
    valid_username,
)

st.set_page_config(
    page_title="IntelliLearn",
    page_icon="📘",
    layout="wide",
)

st.markdown(
    """
    <style>
    .hero {
        padding: 2.5rem 2rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f172a, #1d4ed8);
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 {font-size: 3rem; margin-bottom: .4rem;}
    .hero p {font-size: 1.15rem; opacity: .9;}
    </style>
    """,
    unsafe_allow_html=True,
)

if is_logged_in():
    st.success(f"Welcome back, {st.session_state.get('full_name', 'Student')}!")
    if st.button("Open Dashboard", type="primary"):
        st.switch_page("pages/1_Dashboard.py")
    st.stop()

st.markdown(
    """
    <div class="hero">
        <h1>IntelliLearn</h1>
        <p>AI-Powered Personalized Learning & Document Intelligence Assistant</p>
        <p>Upload → Understand → Practice → Improve</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 1])

with left:
    st.subheader("Learn from your own study material")
    st.write(
        """
        IntelliLearn lets students upload PDFs, ask grounded questions,
        generate quizzes and flashcards, detect weak topics, build study
        plans, and track learning progress using Generative AI + RAG.
        """
    )
    st.markdown(
        """
        **Core modules**
        - Secure registration and email verification
        - PDF document intelligence
        - RAG-based Ask AI with page citations
        - Quiz and flashcard generation
        - Personalized study planner
        - Learning analytics
        """
    )

with right:
    tab_login, tab_register, tab_verify = st.tabs(
        ["Sign in", "Create account", "Verify email"]
    )

    with tab_login:
        with st.form("login_form"):
            identifier = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not identifier or not password:
                st.error("Enter your username and password.")
            else:
                try:
                    sign_in_with_username(identifier, password)
                    st.success("Signed in successfully.")
                    st.switch_page("pages/1_Dashboard.py")
                except Exception as exc:
                    message = str(exc)
                    if "Email not confirmed" in message:
                        st.error("Please verify your email first.")
                    else:
                        st.error(f"Sign in failed: {message}")

    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input("Full name")
            username = st.text_input(
                "Choose a username",
                help="3–30 characters: letters, numbers and underscore only.",
            )
            email = st.text_input("Email")
            password = st.text_input("Create password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not all([full_name, username, email, password, confirm_password]):
                st.error("Please complete every field.")
            elif not valid_username(username):
                st.error("Username must be 3–30 letters, numbers or underscores.")
            elif "@" not in email:
                st.error("Enter a valid email address.")
            elif len(password) < 8:
                st.error("Use a password with at least 8 characters.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    sign_up(full_name, username, email, password)
                    st.session_state.pending_verification_email = email.strip().lower()
                    st.success(
                        "Account created. Check your email for the verification code, "
                        "then open the 'Verify email' tab."
                    )
                except Exception as exc:
                    st.error(f"Registration failed: {exc}")

    with tab_verify:
        default_email = st.session_state.get("pending_verification_email", "")
        with st.form("verify_form"):
            verify_email = st.text_input("Email", value=default_email)
            token = st.text_input(
                "Verification code",
                help="Enter the code sent by Supabase.",
            )
            submitted = st.form_submit_button(
                "Verify email",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not verify_email or not token:
                st.error("Enter the email and verification code.")
            else:
                try:
                    verify_signup_otp(verify_email, token)
                    st.success("Email verified. Your account is ready.")
                    if is_logged_in():
                        st.switch_page("pages/1_Dashboard.py")
                except Exception as exc:
                    st.error(f"Verification failed: {exc}")
