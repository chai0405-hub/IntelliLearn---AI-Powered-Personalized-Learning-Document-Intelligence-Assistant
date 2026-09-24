import time
import streamlit as st

from utils.auth import (
    is_logged_in,
    resend_signup_otp,
    sign_in_with_username,
    sign_up,
    valid_username,
    verify_signup_otp,
)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="IntelliLearn",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

RESEND_COOLDOWN_SECONDS = 60

# ============================================================
# SESSION STATE
# ============================================================
if "auth_view" not in st.session_state:
    st.session_state.auth_view = "signin"

if is_logged_in():
    st.switch_page("pages/1_Dashboard.py")

# ============================================================
# PREMIUM AUTH UI
# ============================================================
st.markdown(
    """
    <style>
    /* ---------------------------------------------------------
       GLOBAL
    --------------------------------------------------------- */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        min-height: 100vh;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 18%, rgba(37, 99, 235, 0.22), transparent 25%),
            radial-gradient(circle at 88% 18%, rgba(124, 58, 237, 0.18), transparent 28%),
            radial-gradient(circle at 80% 86%, rgba(14, 165, 233, 0.16), transparent 24%),
            linear-gradient(135deg, #f8fbff 0%, #eef4ff 42%, #f8fafc 100%);
        position: relative;
        overflow-x: hidden;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.22;
        background-image:
            linear-gradient(rgba(37, 99, 235, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(37, 99, 235, 0.05) 1px, transparent 1px);
        background-size: 34px 34px;
        mask-image: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent 85%);
        -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,0.6), transparent 85%);
    }

    .block-container {
        max-width: 1160px;
        padding-top: 2.3rem;
        padding-bottom: 2.6rem;
    }

    /* ---------------------------------------------------------
       BRAND
    --------------------------------------------------------- */
    .brand-shell {
        text-align: center;
        margin-bottom: 1.6rem;
    }

    .brand-logo {
        width: 70px;
        height: 70px;
        margin: 0 auto 0.9rem auto;
        border-radius: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: white;
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 55%, #7c3aed 100%);
        box-shadow:
            0 16px 34px rgba(37, 99, 235, 0.24),
            inset 0 1px 0 rgba(255,255,255,0.24);
    }

    .brand-title {
        margin: 0;
        color: #0f172a;
        font-size: clamp(2.2rem, 4vw, 3.25rem);
        font-weight: 850;
        letter-spacing: -0.055em;
        line-height: 1;
    }

    .brand-tagline {
        margin-top: 0.65rem;
        color: #475569;
        font-size: 1.02rem;
        font-weight: 500;
    }

    .brand-subline {
        margin-top: 0.28rem;
        color: #64748b;
        font-size: 0.9rem;
    }

    /* ---------------------------------------------------------
       AUTH CARD
    --------------------------------------------------------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 28px !important;
        border: 1px solid rgba(255,255,255,0.72) !important;
        background: rgba(255,255,255,0.84) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow:
            0 30px 70px rgba(15, 23, 42, 0.12),
            0 4px 18px rgba(37, 99, 235, 0.07);
        padding: 0.3rem 0.45rem 0.4rem 0.45rem;
    }

    .auth-kicker {
        display: inline-block;
        margin-bottom: 0.8rem;
        padding: 0.38rem 0.72rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #4338ca;
        font-size: 0.78rem;
        font-weight: 750;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .auth-title {
        color: #0f172a;
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        line-height: 1.15;
        margin-bottom: 0.38rem;
    }

    .auth-copy {
        color: #64748b;
        font-size: 0.96rem;
        line-height: 1.55;
        margin-bottom: 1.15rem;
    }

    /* ---------------------------------------------------------
       INPUTS
    --------------------------------------------------------- */
    label[data-testid="stWidgetLabel"] p {
        color: #334155 !important;
        font-weight: 650 !important;
        font-size: 0.92rem !important;
    }

    div[data-baseweb="input"] > div {
        min-height: 48px;
        border-radius: 14px !important;
        background: rgba(248, 250, 252, 0.92) !important;
        border-color: #dbe3ef !important;
        box-shadow: none !important;
    }

    div[data-baseweb="input"] > div:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    }

    input {
        font-size: 0.96rem !important;
    }

    /* ---------------------------------------------------------
       BUTTONS
    --------------------------------------------------------- */
    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 48px;
        border-radius: 14px !important;
        font-weight: 750 !important;
        transition: all 0.18s ease;
    }

    .stFormSubmitButton > button[kind="primary"],
    .stButton > button[kind="primary"] {
        color: white !important;
        border: 0 !important;
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 60%, #7c3aed 100%) !important;
        box-shadow: 0 10px 24px rgba(37,99,235,0.2);
    }

    .stFormSubmitButton > button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 28px rgba(37,99,235,0.25);
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(248,250,252,0.92) !important;
        color: #334155 !important;
        border: 1px solid #dbe3ef !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        border-color: #93c5fd !important;
        color: #1d4ed8 !important;
        background: #f8fbff !important;
    }

    /* ---------------------------------------------------------
       VERIFY STATE
    --------------------------------------------------------- */
    .verify-icon {
        width: 66px;
        height: 66px;
        margin: 0 auto 0.95rem auto;
        border-radius: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        background: linear-gradient(135deg, #dbeafe, #ede9fe);
        box-shadow: inset 0 0 0 1px rgba(99,102,241,0.08);
    }

    .verify-center {
        text-align: center;
    }

    /* ---------------------------------------------------------
       INFO / SUCCESS / ERROR
    --------------------------------------------------------- */
    div[data-testid="stAlert"] {
        border-radius: 14px;
    }

    /* ---------------------------------------------------------
       DIVIDERS / FOOTER
    --------------------------------------------------------- */
    hr {
        border-color: #e7edf5 !important;
        margin-top: 1.2rem !important;
        margin-bottom: 1.2rem !important;
    }

    .switch-copy {
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 0.35rem;
    }

    .feature-line {
        text-align: center;
        margin-top: 1.2rem;
        color: #64748b;
        font-size: 0.84rem;
        letter-spacing: 0.005em;
    }

    .security-note {
        text-align: center;
        margin-top: 0.45rem;
        color: #94a3b8;
        font-size: 0.76rem;
    }

    /* ---------------------------------------------------------
       MOBILE
    --------------------------------------------------------- */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.35rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .brand-logo {
            width: 62px;
            height: 62px;
            border-radius: 19px;
        }

        .brand-tagline {
            font-size: 0.92rem;
        }

        .brand-subline {
            font-size: 0.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# BRAND HEADER
# ============================================================
st.markdown(
    """
    <div class="brand-shell">
        <div class="brand-logo">IL</div>
        <h1 class="brand-title">IntelliLearn</h1>
        <div class="brand-tagline">
            AI-Powered Personalized Learning & Document Intelligence
        </div>
        <div class="brand-subline">
            Upload → Understand → Practice → Improve
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CENTERED AUTH PANEL
# ============================================================
space_left, auth_col, space_right = st.columns([1.1, 1.35, 1.1])

with auth_col:
    with st.container(border=True):

        # ----------------------------------------------------
        # SIGN IN
        # ----------------------------------------------------
        if st.session_state.auth_view == "signin":
            st.markdown(
                """
                <div class="auth-kicker">Student Portal</div>
                <div class="auth-title">Welcome back</div>
                <div class="auth-copy">
                    Sign in to continue to your personalized learning workspace.
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
                                "Please verify it before signing in."
                            )
                        else:
                            st.error(f"Sign in failed: {message}")

            st.divider()

            st.markdown(
                '<div class="switch-copy">New to IntelliLearn?</div>',
                unsafe_allow_html=True,
            )

            if st.button(
                "Create a new account",
                use_container_width=True,
                key="open_register",
            ):
                st.session_state.auth_view = "register"
                st.rerun()

        # ----------------------------------------------------
        # CREATE ACCOUNT
        # ----------------------------------------------------
        elif st.session_state.auth_view == "register":
            st.markdown(
                """
                <div class="auth-kicker">Get Started</div>
                <div class="auth-title">Create your account</div>
                <div class="auth-copy">
                    Set up your IntelliLearn profile. We will verify your email
                    before activating your account.
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
                    help="3–30 characters. Letters, numbers and underscores only.",
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
                        "letters, numbers or underscores."
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

                        st.session_state.pending_verification_email = clean_email
                        st.session_state.verification_sent_at = time.time()
                        st.session_state.auth_view = "verify"
                        st.rerun()

                    except Exception as exc:
                        st.error(f"Registration failed: {exc}")

            st.divider()

            st.markdown(
                '<div class="switch-copy">Already have an account?</div>',
                unsafe_allow_html=True,
            )

            if st.button(
                "Back to sign in",
                use_container_width=True,
                key="register_back_to_signin",
            ):
                st.session_state.auth_view = "signin"
                st.rerun()

        # ----------------------------------------------------
        # EMAIL VERIFICATION
        # ----------------------------------------------------
        elif st.session_state.auth_view == "verify":
            pending_email = st.session_state.get(
                "pending_verification_email",
                "",
            )

            if not pending_email:
                st.session_state.auth_view = "register"
                st.rerun()

            st.markdown(
                """
                <div class="verify-center">
                    <div class="verify-icon">✉</div>
                    <div class="auth-kicker">Email Verification</div>
                    <div class="auth-title">Check your inbox</div>
                    <div class="auth-copy">
                        Enter the verification code we sent to your email address.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.info(f"Verification code sent to **{pending_email}**")

            with st.form("verification_form", clear_on_submit=False):
                verification_code = st.text_input(
                    "Verification code",
                    placeholder="Enter the latest verification code",
                    help="If you requested another code, use only the newest one.",
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

                        st.session_state.pop(
                            "pending_verification_email",
                            None,
                        )
                        st.session_state.pop(
                            "verification_sent_at",
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
                            "If the code expired, request a new one below."
                        )

            # Resend verification code
            st.caption(
                "Didn't receive the email, or has the code expired?"
            )

            if st.button(
                "Resend verification code",
                use_container_width=True,
                key="resend_otp",
            ):
                last_sent = float(
                    st.session_state.get(
                        "verification_sent_at",
                        0,
                    )
                )

                remaining = RESEND_COOLDOWN_SECONDS - (
                    time.time() - last_sent
                )

                if last_sent and remaining > 0:
                    st.info(
                        f"Please wait {int(remaining) + 1} seconds "
                        "before requesting another code."
                    )
                else:
                    try:
                        resend_signup_otp(pending_email)
                        st.session_state.verification_sent_at = time.time()

                        st.success(
                            "A new verification code has been sent. "
                            "Please use the latest email."
                        )

                    except Exception as exc:
                        st.error(
                            f"Could not resend verification code: {exc}"
                        )

            st.divider()

            if st.button(
                "Back to sign in",
                use_container_width=True,
                key="verify_back_to_signin",
            ):
                st.session_state.auth_view = "signin"
                st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="feature-line">
        RAG-powered document Q&A · AI quizzes · Flashcards · Study planning · Learning analytics
    </div>
    <div class="security-note">
        Secure authentication powered by Supabase
    </div>
    """,
    unsafe_allow_html=True,
)
