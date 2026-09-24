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
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "signin"

# If a user is already authenticated, take them straight to the dashboard.
if is_logged_in():
    st.switch_page("pages/1_Dashboard.py")

# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Hide the multipage sidebar before login */
        section[data-testid="stSidebar"] {
            display: none;
        }

        /* Cleaner app background */
        .stApp {
            background:
                radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.12), transparent 28%),
                radial-gradient(circle at 85% 90%, rgba(79, 70, 229, 0.10), transparent 30%),
                #f8fafc;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        .brand-wrap {
            text-align: center;
            margin-bottom: 1.6rem;
        }

        .brand-badge {
            width: 58px;
            height: 58px;
            margin: 0 auto 0.8rem auto;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            background: linear-gradient(135deg, #1d4ed8, #4f46e5);
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.22);
        }

        .brand-title {
            font-size: 2.35rem;
            line-height: 1.1;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.04em;
            margin: 0;
        }

        .brand-subtitle {
            margin-top: 0.55rem;
            color: #64748b;
            font-size: 1rem;
        }

        .auth-heading {
            font-size: 1.7rem;
            font-weight: 750;
            color: #0f172a;
            margin-bottom: 0.25rem;
        }

        .auth-copy {
            color: #64748b;
            margin-bottom: 1.1rem;
        }

        .mini-note {
            text-align: center;
            color: #64748b;
            font-size: 0.88rem;
            margin-top: 1rem;
        }

        .verify-icon {
            width: 62px;
            height: 62px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem auto;
            background: #dbeafe;
            font-size: 28px;
        }

        /* Softer card borders */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px;
            border-color: #e2e8f0;
            box-shadow: 0 20px 55px rgba(15, 23, 42, 0.08);
            background: rgba(255, 255, 255, 0.97);
        }

        /* Input polish */
        div[data-baseweb="input"] > div {
            border-radius: 12px;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 12px;
            min-height: 44px;
            font-weight: 650;
        }

        /* Keep toolbar visually quiet */
        header[data-testid="stHeader"] {
            background: transparent;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Header / Brand
# ------------------------------------------------------------
st.markdown(
    """
    <div class="brand-wrap">
        <div class="brand-badge">🎓</div>
        <div class="brand-title">IntelliLearn</div>
        <div class="brand-subtitle">
            AI-Powered Personalized Learning & Document Intelligence Assistant
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Centered authentication card
left_space, auth_col, right_space = st.columns([1.15, 1.35, 1.15])

with auth_col:
    with st.container(border=True):

        # ====================================================
        # SIGN IN
        # ====================================================
        if st.session_state.auth_view == "signin":
            st.markdown(
                """
                <div class="auth-heading">Welcome back</div>
                <div class="auth-copy">
                    Sign in to continue learning with your documents.
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("signin_form", clear_on_submit=False):
                identifier = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )

                sign_in_clicked = st.form_submit_button(
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                )

            if sign_in_clicked:
                if not identifier.strip() or not password:
                    st.error("Please enter your username and password.")
                else:
                    try:
                        sign_in_with_username(identifier, password)
                        st.success("Signed in successfully.")
                        st.switch_page("pages/1_Dashboard.py")
                    except Exception as exc:
                        message = str(exc)
                        if "Email not confirmed" in message:
                            st.warning(
                                "Your email has not been verified yet. "
                                "Create the account again if you need a new verification code."
                            )
                        else:
                            st.error(f"Sign in failed: {message}")

            st.divider()
            st.markdown(
                "<div style='text-align:center;color:#64748b;'>New to IntelliLearn?</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Create an account",
                use_container_width=True,
                key="go_to_register",
            ):
                st.session_state.auth_view = "register"
                st.rerun()

        # ====================================================
        # CREATE ACCOUNT
        # ====================================================
        elif st.session_state.auth_view == "register":
            st.markdown(
                """
                <div class="auth-heading">Create your account</div>
                <div class="auth-copy">
                    Create a student account to start learning with IntelliLearn.
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input(
                    "Full name",
                    placeholder="Enter your full name",
                )
                username = st.text_input(
                    "Username",
                    placeholder="Choose a unique username",
                    help="3–30 characters. Use letters, numbers, or underscores.",
                )
                email = st.text_input(
                    "Email address",
                    placeholder="you@example.com",
                )
                password = st.text_input(
                    "Create password",
                    type="password",
                    placeholder="Minimum 8 characters",
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password",
                )

                create_clicked = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                )

            if create_clicked:
                if not all(
                    [
                        full_name.strip(),
                        username.strip(),
                        email.strip(),
                        password,
                        confirm_password,
                    ]
                ):
                    st.error("Please complete every field.")
                elif not valid_username(username):
                    st.error(
                        "Username must be 3–30 characters and contain only "
                        "letters, numbers, or underscores."
                    )
                elif "@" not in email or "." not in email.split("@")[-1]:
                    st.error("Please enter a valid email address.")
                elif len(password) < 8:
                    st.error("Password must contain at least 8 characters.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        clean_email = email.strip().lower()
                        sign_up(
                            full_name.strip(),
                            username.strip(),
                            clean_email,
                            password,
                        )

                        # Store only what is needed for the verification screen.
                        st.session_state.pending_verification_email = clean_email

                        # Verification page appears ONLY after successful signup.
                        st.session_state.auth_view = "verify"
                        st.rerun()

                    except Exception as exc:
                        st.error(f"Registration failed: {exc}")

            st.divider()
            st.markdown(
                "<div style='text-align:center;color:#64748b;'>Already have an account?</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "Back to sign in",
                use_container_width=True,
                key="back_to_signin_from_register",
            ):
                st.session_state.auth_view = "signin"
                st.rerun()

        # ====================================================
        # VERIFY EMAIL
        # ====================================================
        elif st.session_state.auth_view == "verify":
            pending_email = st.session_state.get(
                "pending_verification_email",
                "",
            )

            # If somebody somehow reaches this state without first registering,
            # return them to the registration page.
            if not pending_email:
                st.session_state.auth_view = "register"
                st.rerun()

            st.markdown(
                """
                <div class="verify-icon">✉️</div>
                <div class="auth-heading" style="text-align:center;">
                    Verify your email
                </div>
                <div class="auth-copy" style="text-align:center;">
                    We sent a verification code to your email address.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.info(f"Verification code sent to **{pending_email}**")

            with st.form("verification_form", clear_on_submit=False):
                verification_code = st.text_input(
                    "Verification code",
                    placeholder="Enter the code from your email",
                    help="Use the latest verification code you received.",
                )

                verify_clicked = st.form_submit_button(
                    "Verify email",
                    type="primary",
                    use_container_width=True,
                )

            if verify_clicked:
                if not verification_code.strip():
                    st.error("Please enter the verification code.")
                else:
                    try:
                        verify_signup_otp(
                            pending_email,
                            verification_code.strip(),
                        )

                        # verify_signup_otp stores the logged-in user when
                        # Supabase returns a session.
                        st.session_state.pop(
                            "pending_verification_email",
                            None,
                        )

                        st.success("Email verified successfully.")

                        if is_logged_in():
                            st.switch_page("pages/1_Dashboard.py")
                        else:
                            st.session_state.auth_view = "signin"
                            st.rerun()

                    except Exception as exc:
                        st.error(
                            f"Verification failed: {exc}. "
                            "Please make sure you are using the latest code."
                        )

            st.divider()
            if st.button(
                "Back to sign in",
                use_container_width=True,
                key="back_to_signin_from_verify",
            ):
                st.session_state.auth_view = "signin"
                st.rerun()

# ------------------------------------------------------------
# Small footer
# ------------------------------------------------------------
st.markdown(
    """
    <div class="mini-note">
        Upload PDFs · Ask with RAG · Generate quizzes · Build study plans · Track progress
    </div>
    """,
    unsafe_allow_html=True,
)
