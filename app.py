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
# HTML HELPER
# Prevents Streamlit from displaying HTML as a code block
# ============================================================

def raw_html(html: str):
    compact_html = " ".join(
        line.strip()
        for line in html.splitlines()
        if line.strip()
    )

    st.markdown(
        compact_html,
        unsafe_allow_html=True,
    )


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

def auth_page():

    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "signin"

    # ========================================================
    # PAGE CSS
    # ========================================================

    st.markdown(
        """
<style>

/* ==========================================================
   HIDE SIDEBAR BEFORE LOGIN
========================================================== */

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


/* ==========================================================
   MAIN BACKGROUND
========================================================== */

.stApp {

    min-height: 100vh;

    background:

        radial-gradient(
            circle at 10% 15%,
            rgba(139, 92, 246, 0.24),
            transparent 30%
        ),

        radial-gradient(
            circle at 88% 15%,
            rgba(59, 130, 246, 0.22),
            transparent 30%
        ),

        radial-gradient(
            circle at 78% 88%,
            rgba(236, 72, 153, 0.14),
            transparent 27%
        ),

        linear-gradient(
            135deg,
            #FCF8FF 0%,
            #EEF2FF 48%,
            #F8FAFC 100%
        );
}


.block-container {

    max-width: 1150px;

    padding-top: 2rem;

    padding-bottom: 3rem;
}


/* ==========================================================
   BRAND
========================================================== */

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

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 22px;

    color: #FFFFFF !important;

    font-size: 1.35rem;

    font-weight: 900;

    background:

        linear-gradient(
            135deg,
            #7C3AED 0%,
            #4F46E5 55%,
            #2563EB 100%
        );

    box-shadow:

        0 18px 42px
        rgba(79, 70, 229, 0.28);
}


.brand-wrapper .brand-title {

    margin: 0;

    color: #17132B !important;

    opacity: 1 !important;

    font-size:
        clamp(
            2.4rem,
            5vw,
            3.35rem
        );

    font-weight: 850;

    letter-spacing: -0.055em;

    line-height: 1;
}


.brand-wrapper .brand-subtitle {

    margin-top: 0.75rem;

    color: #4B4663 !important;

    opacity: 1 !important;

    font-size: 1.05rem;

    font-weight: 600;
}


.brand-wrapper .brand-small {

    margin-top: 0.30rem;

    color: #7C758F !important;

    opacity: 1 !important;

    font-size: 0.88rem;
}


/* ==========================================================
   GLASS AUTH CARD
========================================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {

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
            0.88
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


/* ==========================================================
   AUTH BADGE
========================================================== */

.auth-badge {

    display: inline-block;

    margin-bottom: 0.85rem;

    padding:
        0.40rem
        0.78rem;

    border-radius: 999px;

    background: #F3E8FF;

    color: #6D28D9 !important;

    opacity: 1 !important;

    font-size: 0.76rem;

    font-weight: 800;

    letter-spacing: 0.04em;

    text-transform: uppercase;
}


/* ==========================================================
   AUTH HEADING
========================================================== */

.auth-title {

    margin-bottom: 0.42rem;

    color: #17132B !important;

    opacity: 1 !important;

    font-size: 1.95rem;

    font-weight: 800;

    letter-spacing: -0.035em;
}


.auth-description {

    margin-bottom: 1.20rem;

    color: #625C76 !important;

    opacity: 1 !important;

    font-size: 0.96rem;

    line-height: 1.55;
}


/* ==========================================================
   FORM LABELS
========================================================== */

label[data-testid="stWidgetLabel"] p {

    color: #2F2942 !important;

    opacity: 1 !important;

    font-weight: 650 !important;

    font-size: 0.93rem !important;
}


/* ==========================================================
   INPUT BOXES
========================================================== */

div[data-baseweb="input"] > div {

    min-height: 48px;

    border-radius:
        14px !important;

    background:

        rgba(
            250,
            250,
            255,
            0.96
        ) !important;
}


input {

    font-size:
        0.96rem !important;
}


/* ==========================================================
   BUTTONS
========================================================== */

.stButton > button,
.stFormSubmitButton > button {

    min-height: 48px;

    border-radius:
        14px !important;

    font-weight:
        750 !important;

    transition:
        all 0.18s ease;
}


/* PRIMARY BUTTON */

.stFormSubmitButton
> button[kind="primary"] {

    border:
        none !important;

    color:
        #FFFFFF !important;

    background:

        linear-gradient(
            135deg,
            #7C3AED 0%,
            #4F46E5 55%,
            #2563EB 100%
        ) !important;

    box-shadow:

        0 10px 25px
        rgba(
            99,
            102,
            241,
            0.24
        );
}


.stFormSubmitButton
> button[kind="primary"]:hover {

    transform:
        translateY(-1px);

    box-shadow:

        0 14px 30px
        rgba(
            99,
            102,
            241,
            0.30
        );
}


/* SECONDARY BUTTON */

.stButton
> button:not([kind="primary"]) {

    background:
        #FAF9FF !important;

    color:
        #4C1D95 !important;

    border:

        1px solid
        #DDD6FE !important;
}


.stButton
> button:not([kind="primary"]):hover {

    color:
        #6D28D9 !important;

    background:
        #F5F3FF !important;

    border-color:
        #C4B5FD !important;
}


/* ==========================================================
   CAPTIONS
========================================================== */

div[data-testid="stCaptionContainer"],
div[data-testid="stCaptionContainer"] p {

    color: #5B5674 !important;

    opacity: 1 !important;
}


/* ==========================================================
   VERIFICATION PAGE
========================================================== */

.verify-center {

    text-align: center;
}


.verify-icon {

    width: 68px;

    height: 68px;

    margin:
        0 auto
        1rem auto;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 22px;

    font-size: 1.85rem;

    color: #4F46E5 !important;

    background:

        linear-gradient(
            135deg,
            #DBEAFE,
            #F3E8FF
        );
}


/* ==========================================================
   ALERTS
========================================================== */

div[data-testid="stAlert"] {

    border-radius:
        14px;
}


/* ==========================================================
   DIVIDER
========================================================== */

hr {

    border-color:
        rgba(
            99,
            102,
            241,
            0.12
        ) !important;
}


/* ==========================================================
   FOOTER
========================================================== */

.footer-features {

    margin-top: 1.35rem;

    text-align: center;

    color: #6B647D !important;

    opacity: 1 !important;

    font-size: 0.84rem;
}


.footer-security {

    margin-top: 0.35rem;

    text-align: center;

    color: #8E879F !important;

    opacity: 1 !important;

    font-size: 0.75rem;
}


/* ==========================================================
   MOBILE
========================================================== */

@media (
    max-width: 768px
) {

    .block-container {

        padding-top:
            1.25rem;

        padding-left:
            1rem;

        padding-right:
            1rem;
    }


    .brand-logo {

        width:
            62px;

        height:
            62px;

        border-radius:
            19px;
    }


    .brand-wrapper .brand-subtitle {

        font-size:
            0.94rem;
    }


    .brand-wrapper .brand-small {

        font-size:
            0.80rem;
    }
}

</style>
""",
        unsafe_allow_html=True,
    )


    # ========================================================
    # BRAND HEADER
    # ========================================================

    raw_html(
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
                &amp; Document Intelligence
            </div>

            <div class="brand-small">
                Upload → Understand → Practice → Improve
            </div>

        </div>
        """
    )


    # ========================================================
    # CENTER LOGIN CARD
    # ========================================================

    left_col, auth_col, right_col = (
        st.columns(
            [
                1.1,
                1.35,
                1.1,
            ]
        )
    )


    with auth_col:

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


                raw_html(
                    """
                    <div class="auth-badge">
                        Student Portal
                    </div>

                    <div class="auth-title">
                        Welcome back
                    </div>

                    <div class="auth-description">
                        Sign in to continue to your personalized
                        learning workspace.
                    </div>
                    """
                )


                with st.form(
                    "signin_form",
                    clear_on_submit=False,
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


                    sign_in_clicked = (
                        st.form_submit_button(
                            "Sign in",
                            type="primary",
                            use_container_width=True,
                        )
                    )


                if sign_in_clicked:


                    if (
                        not identifier.strip()
                        or not password
                    ):


                        st.error(
                            "Please enter your "
                            "username and password."
                        )


                    else:


                        try:


                            sign_in_with_username(
                                identifier,
                                password,
                            )


                            st.rerun()


                        except Exception as exc:


                            message = str(
                                exc
                            )


                            if (
                                "Email not confirmed"
                                in message
                            ):


                                st.warning(
                                    "Your email has not "
                                    "been verified yet."
                                )


                            else:


                                st.error(
                                    "Sign in failed: "
                                    f"{message}"
                                )


                st.divider()


                st.caption(
                    "New to IntelliLearn?"
                )


                if st.button(
                    "Create a new account",
                    use_container_width=True,
                    key="go_register",
                ):


                    st.session_state.auth_view = (
                        "register"
                    )


                    st.rerun()



            # ====================================================
            # CREATE ACCOUNT
            # ====================================================

            elif (
                st.session_state.auth_view
                == "register"
            ):


                raw_html(
                    """
                    <div class="auth-badge">
                        Get Started
                    </div>

                    <div class="auth-title">
                        Create your account
                    </div>

                    <div class="auth-description">
                        Create your student profile and verify
                        your email to start using IntelliLearn.
                    </div>
                    """
                )


                with st.form(
                    "register_form",
                    clear_on_submit=False,
                ):


                    full_name = (
                        st.text_input(
                            "Full name",
                            placeholder=(
                                "Enter your full name"
                            ),
                        )
                    )


                    username = (
                        st.text_input(
                            "Username",
                            placeholder=(
                                "Choose a unique username"
                            ),
                            help=(
                                "3–30 characters. "
                                "Letters, numbers "
                                "and underscores only."
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
                                "Minimum 8 characters"
                            ),
                        )
                    )


                    confirm_password = (
                        st.text_input(
                            "Confirm password",
                            type="password",
                            placeholder=(
                                "Re-enter your password"
                            ),
                        )
                    )


                    create_clicked = (
                        st.form_submit_button(
                            "Create account",
                            type="primary",
                            use_container_width=True,
                        )
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


                        st.error(
                            "Please complete "
                            "every field."
                        )


                    elif not valid_username(
                        username
                    ):


                        st.error(
                            "Username must be "
                            "3–30 characters and "
                            "contain only letters, "
                            "numbers or underscores."
                        )


                    elif (
                        "@"
                        not in email
                        or "."
                        not in email.split("@")[-1]
                    ):


                        st.error(
                            "Please enter "
                            "a valid email address."
                        )


                    elif (
                        len(password)
                        < 8
                    ):


                        st.error(
                            "Password must contain "
                            "at least 8 characters."
                        )


                    elif (
                        password
                        != confirm_password
                    ):


                        st.error(
                            "Passwords do not match."
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


                st.caption(
                    "Already have an account?"
                )


                if st.button(
                    "Back to sign in",
                    use_container_width=True,
                    key="register_back",
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


                raw_html(
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
                            Enter the latest verification code
                            sent to your email.
                        </div>

                    </div>
                    """
                )


                st.info(
                    "Verification code sent to "
                    f"**{pending_email}**"
                )


                with st.form(
                    "verify_form",
                    clear_on_submit=False,
                ):


                    verification_code = (
                        st.text_input(
                            "Verification code",
                            placeholder=(
                                "Enter the latest "
                                "verification code"
                            ),
                            help=(
                                "If you requested "
                                "a new code, always "
                                "use the latest one."
                            ),
                        )
                    )


                    verify_clicked = (
                        st.form_submit_button(
                            "Verify email",
                            type="primary",
                            use_container_width=True,
                        )
                    )


                if verify_clicked:


                    if not (
                        verification_code
                        .strip()
                    ):


                        st.error(
                            "Please enter the "
                            "verification code."
                        )


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
                    key="resend_code",
                ):


                    last_sent = float(
                        st.session_state.get(
                            "verification_sent_at",
                            0,
                        )
                    )


                    remaining = (
                        RESEND_COOLDOWN_SECONDS
                        -
                        (
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
                            "seconds before requesting "
                            "another code."
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
                                "A new verification code "
                                "has been sent. "
                                "Use the newest code."
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
                    key="verify_back",
                ):


                    st.session_state.auth_view = (
                        "signin"
                    )


                    st.rerun()



    # ========================================================
    # FOOTER
    # ========================================================

    raw_html(
        """
        <div class="footer-features">
            RAG Document Q&amp;A ·
            AI Quizzes ·
            Flashcards ·
            Study Planning ·
            Learning Analytics
        </div>

        <div class="footer-security">
            Secure authentication powered by Supabase
        </div>
        """
    )



# ============================================================
# PAGE DEFINITIONS
# ============================================================


login_page = st.Page(
    auth_page,
    title="IntelliLearn",
    icon="🎓",
    url_path="login",
)


dashboard_page = st.Page(
    "pages/1_Dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    url_path="dashboard",
)


documents_page = st.Page(
    "pages/2_My_Documents.py",
    title="My Documents",
    icon=":material/folder:",
    url_path="documents",
)


ask_page = st.Page(
    "pages/3_Ask_IntelliLearn.py",
    title="Ask IntelliLearn",
    icon=":material/smart_toy:",
    url_path="ask",
)


quiz_page = st.Page(
    "pages/4_Quiz.py",
    title="Quiz",
    icon=":material/quiz:",
    url_path="quiz",
)


flashcards_page = st.Page(
    "pages/5_Flashcards.py",
    title="Flashcards",
    icon=":material/style:",
    url_path="flashcards",
)


study_plan_page = st.Page(
    "pages/6_Study_Plan.py",
    title="Study Plan",
    icon=":material/calendar_month:",
    url_path="study-plan",
)


progress_page = st.Page(
    "pages/7_Progress.py",
    title="Progress",
    icon=":material/monitoring:",
    url_path="progress",
)



# ============================================================
# ROUTING
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
