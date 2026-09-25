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
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="IntelliLearn",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

RESEND_COOLDOWN_SECONDS = 60


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

def auth_page():

    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "signin"

    # --------------------------------------------------------
    # AUTH PAGE CSS
    # --------------------------------------------------------

    st.markdown(
        """
        <style>

        /* Hide sidebar completely before login */
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        .stApp {
            min-height: 100vh;

            background:
                radial-gradient(
                    circle at 10% 15%,
                    rgba(139, 92, 246, 0.22),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 90% 20%,
                    rgba(59, 130, 246, 0.20),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 80% 85%,
                    rgba(236, 72, 153, 0.12),
                    transparent 25%
                ),
                linear-gradient(
                    135deg,
                    #FAF7FF 0%,
                    #EEF2FF 45%,
                    #F8FAFC 100%
                );
        }

        .block-container {
            max-width: 1150px;
            padding-top: 2.4rem;
            padding-bottom: 3rem;
        }

        /* ===========================
           BRAND
        =========================== */

        .brand-wrapper {
            text-align: center;
            margin-bottom: 1.8rem;
        }

        .brand-logo {
            width: 72px;
            height: 72px;

            margin:
                0 auto
                1rem auto;

            border-radius: 22px;

            display: flex;
            align-items: center;
            justify-content: center;

            color: white;

            font-size: 1.35rem;
            font-weight: 900;

            background:
                linear-gradient(
                    135deg,
                    #7C3AED,
                    #4F46E5,
                    #2563EB
                );

            box-shadow:
                0 18px 40px
                rgba(99, 102, 241, 0.30);
        }

        .brand-title {
            margin: 0;

            color: #17132B;

            font-size: 3rem;

            font-weight: 850;

            letter-spacing: -0.055em;

            line-height: 1;
        }

        .brand-subtitle {
            margin-top: 0.7rem;

            color: #5B5674;

            font-size: 1.03rem;

            font-weight: 500;
        }

        .brand-small {
            margin-top: 0.25rem;

            color: #8B86A0;

            font-size: 0.86rem;
        }

        /* ===========================
           AUTH CARD
        =========================== */

        div[
            data-testid="stVerticalBlockBorderWrapper"
        ] {
            border-radius: 28px !important;

            border:
                1px solid
                rgba(
                    255,
                    255,
                    255,
                    0.72
                ) !important;

            background:
                rgba(
                    255,
                    255,
                    255,
                    0.86
                ) !important;

            backdrop-filter:
                blur(20px);

            -webkit-backdrop-filter:
                blur(20px);

            box-shadow:
                0 30px 70px
                rgba(
                    30,
                    41,
                    59,
                    0.12
                );
        }

        .auth-badge {
            display: inline-block;

            padding:
                0.4rem
                0.75rem;

            margin-bottom:
                0.85rem;

            border-radius:
                999px;

            color:
                #6D28D9;

            background:
                #F3E8FF;

            font-size:
                0.76rem;

            font-weight:
                800;

            letter-spacing:
                0.04em;

            text-transform:
                uppercase;
        }

        .auth-title {
            color:
                #17132B;

            font-size:
                1.9rem;

            font-weight:
                800;

            letter-spacing:
                -0.035em;

            margin-bottom:
                0.4rem;
        }

        .auth-description {
            color:
                #6B6880;

            font-size:
                0.96rem;

            line-height:
                1.55;

            margin-bottom:
                1.2rem;
        }

        /* ===========================
           INPUTS
        =========================== */

        label[
            data-testid="stWidgetLabel"
        ] p {
            color:
                #403B55 !important;

            font-weight:
                650 !important;
        }

        div[
            data-baseweb="input"
        ] > div {
            min-height:
                48px;

            border-radius:
                14px !important;

            background:
                rgba(
                    250,
                    250,
                    255,
                    0.95
                ) !important;
        }

        input {
            font-size:
                0.96rem !important;
        }

        /* ===========================
           BUTTONS
        =========================== */

        .stButton > button,
        .stFormSubmitButton > button {

            min-height:
                48px;

            border-radius:
                14px !important;

            font-weight:
                750 !important;
        }

        .stFormSubmitButton
        > button[
            kind="primary"
        ] {

            background:
                linear-gradient(
                    135deg,
                    #7C3AED,
                    #4F46E5,
                    #2563EB
                ) !important;

            color:
                white !important;

            border:
                none !important;

            box-shadow:
                0 10px 26px
                rgba(
                    99,
                    102,
                    241,
                    0.25
                );
        }

        .stButton
        > button:not(
            [kind="primary"]
        ) {

            background:
                #FAF9FF !important;

            color:
                #4C1D95 !important;

            border:
                1px solid
                #DDD6FE !important;
        }

        /* ===========================
           VERIFY PAGE
        =========================== */

        .verify-icon {
            width:
                66px;

            height:
                66px;

            margin:
                0 auto
                1rem auto;

            border-radius:
                22px;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            font-size:
                1.8rem;

            background:
                linear-gradient(
                    135deg,
                    #DBEAFE,
                    #F3E8FF
                );
        }

        .verify-center {
            text-align:
                center;
        }

        /* ===========================
           FOOTER
        =========================== */

        .footer-features {
            text-align:
                center;

            margin-top:
                1.4rem;

            color:
                #78738D;

            font-size:
                0.84rem;
        }

        .footer-security {
            text-align:
                center;

            margin-top:
                0.4rem;

            color:
                #A09BAF;

            font-size:
                0.74rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="brand-wrapper">

            <div class="brand-logo">
                IL
            </div>

            <h1 class="brand-title">
                IntelliLearn
            </h1>

            <div class="brand-subtitle">
                AI-Powered Personalized Learning
                & Document Intelligence
            </div>

            <div class="brand-small">
                Upload → Understand → Practice → Improve
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns(
        [
            1.1,
            1.35,
            1.1,
        ]
    )

    with center:

        with st.container(
            border=True
        ):

            # ====================================================
            # SIGN IN
            # ====================================================

            if (
                st.session_state.auth_view
                == "signin"
            ):

                st.markdown(
                    """
                    <div class="auth-badge">
                        Student Portal
                    </div>

                    <div class="auth-title">
                        Welcome back
                    </div>

                    <div class="auth-description">
                        Sign in to continue to your
                        personalized learning workspace.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form(
                    "signin_form"
                ):

                    identifier = (
                        st.text_input(
                            "Username",
                            placeholder=(
                                "Enter your username"
                            ),
                        )
                    )

                    password = (
                        st.text_input(
                            "Password",
                            type="password",
                            placeholder=(
                                "Enter your password"
                            ),
                        )
                    )

                    signin = (
                        st.form_submit_button(
                            "Sign in",
                            type="primary",
                            use_container_width=True,
                        )
                    )

                if signin:

                    if (
                        not identifier.strip()
                        or not password
                    ):

                        st.error(
                            "Please enter "
                            "your username "
                            "and password."
                        )

                    else:

                        try:

                            sign_in_with_username(
                                identifier,
                                password,
                            )

                            st.rerun()

                        except Exception as exc:

                            error_message = str(
                                exc
                            )

                            if (
                                "Email not confirmed"
                                in error_message
                            ):

                                st.warning(
                                    "Your email "
                                    "has not been "
                                    "verified yet."
                                )

                            else:

                                st.error(
                                    "Sign in failed: "
                                    f"{error_message}"
                                )

                st.divider()

                st.caption(
                    "New to IntelliLearn?"
                )

                if st.button(
                    "Create a new account",
                    use_container_width=True,
                    key="register_button",
                ):

                    st.session_state.auth_view = (
                        "register"
                    )

                    st.rerun()

            # ====================================================
            # REGISTER
            # ====================================================

            elif (
                st.session_state.auth_view
                == "register"
            ):

                st.markdown(
                    """
                    <div class="auth-badge">
                        Get Started
                    </div>

                    <div class="auth-title">
                        Create your account
                    </div>

                    <div class="auth-description">
                        Create your student profile
                        and verify your email to
                        start using IntelliLearn.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form(
                    "register_form"
                ):

                    full_name = (
                        st.text_input(
                            "Full name",
                            placeholder=(
                                "Enter your "
                                "full name"
                            ),
                        )
                    )

                    username = (
                        st.text_input(
                            "Username",
                            placeholder=(
                                "Choose a "
                                "unique username"
                            ),
                        )
                    )

                    email = (
                        st.text_input(
                            "Email address",
                            placeholder=(
                                "you@example.com"
                            ),
                        )
                    )

                    password = (
                        st.text_input(
                            "Create password",
                            type="password",
                            placeholder=(
                                "Minimum "
                                "8 characters"
                            ),
                        )
                    )

                    confirm_password = (
                        st.text_input(
                            "Confirm password",
                            type="password",
                            placeholder=(
                                "Re-enter "
                                "your password"
                            ),
                        )
                    )

                    create_account = (
                        st.form_submit_button(
                            "Create account",
                            type="primary",
                            use_container_width=True,
                        )
                    )

                if create_account:

                    if not all(
                        [
                            full_name.strip(),
                            username.strip(),
                            email.strip(),
                            password,
                            confirm_password,
                        ]
                    ):

                        st.error(
                            "Please complete "
                            "every field."
                        )

                    elif not valid_username(
                        username
                    ):

                        st.error(
                            "Username must be "
                            "3–30 characters "
                            "and contain only "
                            "letters, numbers "
                            "or underscores."
                        )

                    elif (
                        "@"
                        not in email
                    ):

                        st.error(
                            "Please enter "
                            "a valid "
                            "email address."
                        )

                    elif (
                        len(password)
                        < 8
                    ):

                        st.error(
                            "Password must "
                            "contain at least "
                            "8 characters."
                        )

                    elif (
                        password
                        != confirm_password
                    ):

                        st.error(
                            "Passwords "
                            "do not match."
                        )

                    else:

                        try:

                            clean_email = (
                                email
                                .strip()
                                .lower()
                            )

                            sign_up(
                                full_name.strip(),
                                username.strip(),
                                clean_email,
                                password,
                            )

                            st.session_state[
                                "pending_verification_email"
                            ] = clean_email

                            st.session_state[
                                "verification_sent_at"
                            ] = time.time()

                            st.session_state.auth_view = (
                                "verify"
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Registration failed: "
                                f"{exc}"
                            )

                st.divider()

                if st.button(
                    "Back to sign in",
                    use_container_width=True,
                    key="back_login",
                ):

                    st.session_state.auth_view = (
                        "signin"
                    )

                    st.rerun()

            # ====================================================
            # VERIFY EMAIL
            # ====================================================

            elif (
                st.session_state.auth_view
                == "verify"
            ):

                pending_email = (
                    st.session_state.get(
                        "pending_verification_email",
                        "",
                    )
                )

                if not pending_email:

                    st.session_state.auth_view = (
                        "register"
                    )

                    st.rerun()

                st.markdown(
                    """
                    <div class="verify-center">

                        <div class="verify-icon">
                            ✉
                        </div>

                        <div class="auth-badge">
                            Email Verification
                        </div>

                        <div class="auth-title">
                            Check your inbox
                        </div>

                        <div class="auth-description">
                            Enter the latest
                            verification code
                            sent to your email.
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.info(
                    "Verification code sent to "
                    f"**{pending_email}**"
                )

                with st.form(
                    "verification_form"
                ):

                    code = (
                        st.text_input(
                            "Verification code",
                            placeholder=(
                                "Enter the "
                                "latest code"
                            ),
                        )
                    )

                    verify = (
                        st.form_submit_button(
                            "Verify email",
                            type="primary",
                            use_container_width=True,
                        )
                    )

                if verify:

                    if not code.strip():

                        st.error(
                            "Please enter "
                            "the verification code."
                        )

                    else:

                        try:

                            verify_signup_otp(
                                pending_email,
                                code.strip(),
                            )

                            st.session_state.pop(
                                "pending_verification_email",
                                None,
                            )

                            st.session_state.pop(
                                "verification_sent_at",
                                None,
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Verification failed: "
                                f"{exc}"
                            )

                st.caption(
                    "Didn't receive the email "
                    "or has the code expired?"
                )

                if st.button(
                    "Resend verification code",
                    use_container_width=True,
                    key="resend_button",
                ):

                    last_sent = float(
                        st.session_state.get(
                            "verification_sent_at",
                            0,
                        )
                    )

                    remaining = (
                        RESEND_COOLDOWN_SECONDS
                        - (
                            time.time()
                            - last_sent
                        )
                    )

                    if (
                        last_sent
                        and remaining > 0
                    ):

                        st.info(
                            "Please wait "
                            f"{int(remaining) + 1} "
                            "seconds before "
                            "requesting another code."
                        )

                    else:

                        try:

                            resend_signup_otp(
                                pending_email
                            )

                            st.session_state[
                                "verification_sent_at"
                            ] = time.time()

                            st.success(
                                "A new verification "
                                "code has been sent."
                            )

                        except Exception as exc:

                            st.error(
                                "Could not resend "
                                "verification code: "
                                f"{exc}"
                            )

                st.divider()

                if st.button(
                    "Back to sign in",
                    use_container_width=True,
                    key="verify_back_login",
                ):

                    st.session_state.auth_view = (
                        "signin"
                    )

                    st.rerun()

    st.markdown(
        """
        <div class="footer-features">
            RAG Document Q&A · AI Quizzes ·
            Flashcards · Study Planning ·
            Learning Analytics
        </div>

        <div class="footer-security">
            Secure authentication powered by Supabase
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE DEFINITIONS
# ============================================================

login_page = st.Page(
    auth_page,
    title="IntelliLearn",
    icon="🎓",
    url_path="login",
    default=True,
)


dashboard_page = st.Page(
    "views/1_Dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    url_path="dashboard",
    default=True,
)


documents_page = st.Page(
    "views/2_My_Documents.py",
    title="My Documents",
    icon=":material/folder:",
    url_path="documents",
)


ask_page = st.Page(
    "views/3_Ask_IntelliLearn.py",
    title="Ask IntelliLearn",
    icon=":material/smart_toy:",
    url_path="ask",
)


quiz_page = st.Page(
    "views/4_Quiz.py",
    title="Quiz",
    icon=":material/quiz:",
    url_path="quiz",
)


flashcards_page = st.Page(
    "views/5_Flashcards.py",
    title="Flashcards",
    icon=":material/style:",
    url_path="flashcards",
)


study_plan_page = st.Page(
    "views/6_Study_Plan.py",
    title="Study Plan",
    icon=":material/calendar_month:",
    url_path="study-plan",
)


progress_page = st.Page(
    "views/7_Progress.py",
    title="Progress",
    icon=":material/monitoring:",
    url_path="progress",
)


# ============================================================
# HIDDEN STREAMLIT NAVIGATION
# ============================================================

if is_logged_in():

    available_pages = [
        dashboard_page,
        documents_page,
        ask_page,
        quiz_page,
        flashcards_page,
        study_plan_page,
        progress_page,
    ]

else:

    available_pages = [
        login_page
    ]


navigation = st.navigation(
    available_pages,
    position="hidden",
)


navigation.run()
