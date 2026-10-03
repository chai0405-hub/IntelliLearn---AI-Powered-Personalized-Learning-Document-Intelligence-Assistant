import time
import streamlit as st

from utils.auth import (
    is_logged_in,
    resend_signup_otp,
    send_password_reset_email,
    sign_in_with_username,
    sign_up,
    update_recovery_password,
    valid_username,
    verify_password_recovery,
    verify_signup_otp,
)

st.set_page_config(
    page_title="IntelliLearn",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

RESEND_COOLDOWN_SECONDS = 60
PASSWORD_RESET_REDIRECT_URL = (
    st.secrets["APP_URL"]
    if "APP_URL" in st.secrets
    else "https://intellilearn-0405.streamlit.app/"
)


def raw_html(html: str):
    html = " ".join(line.strip() for line in html.splitlines() if line.strip())
    st.markdown(html, unsafe_allow_html=True)


def auth_page():
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "signin"

    # Handle reset-password link from Supabase email.
    token_hash = st.query_params.get("token_hash")
    recovery_type = st.query_params.get("type")

    if token_hash and recovery_type == "recovery" and not st.session_state.get("recovery_verified"):
        try:
            verify_password_recovery(token_hash)
            st.session_state.recovery_verified = True
            st.session_state.auth_view = "reset_password"
            st.query_params.clear()
            st.rerun()
        except Exception:
            st.session_state.auth_view = "forgot_password"
            st.session_state.recovery_error = True
            st.query_params.clear()
            st.rerun()

    st.markdown(
        """
<style>
section[data-testid="stSidebar"]{display:none!important;}
header[data-testid="stHeader"]{background:transparent!important;}
#MainMenu,footer{visibility:hidden;}
.stApp{
 min-height:100vh;
 background:
 radial-gradient(circle at 10% 15%,rgba(139,92,246,.24),transparent 30%),
 radial-gradient(circle at 88% 15%,rgba(59,130,246,.22),transparent 30%),
 radial-gradient(circle at 78% 88%,rgba(236,72,153,.14),transparent 27%),
 linear-gradient(135deg,#FCF8FF 0%,#EEF2FF 48%,#F8FAFC 100%);
}
.block-container{max-width:1150px;padding-top:2rem;padding-bottom:3rem;}
.brand-wrapper{text-align:center;margin-bottom:1.8rem;}
.brand-logo{
 width:72px;height:72px;margin:0 auto 1rem auto;display:flex;align-items:center;justify-content:center;
 border-radius:22px;color:#fff!important;font-size:1.35rem;font-weight:900;
 background:linear-gradient(135deg,#7C3AED,#4F46E5 55%,#2563EB);
 box-shadow:0 18px 42px rgba(79,70,229,.28);
}
.brand-title{margin:0;color:#17132B!important;font-size:clamp(2.4rem,5vw,3.35rem);font-weight:850;letter-spacing:-.055em;line-height:1;}
.brand-subtitle{margin-top:.75rem;color:#4B4663!important;font-size:1.05rem;font-weight:600;}
.brand-small{margin-top:.3rem;color:#7C758F!important;font-size:.88rem;}
div[data-testid="stVerticalBlockBorderWrapper"]{
 border-radius:28px!important;border:1px solid rgba(255,255,255,.72)!important;
 background:rgba(255,255,255,.88)!important;box-shadow:0 30px 70px rgba(30,41,59,.12);
}
.auth-badge{
 display:inline-block;margin-bottom:.85rem;padding:.4rem .78rem;border-radius:999px;
 background:#F3E8FF;color:#6D28D9!important;font-size:.76rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase;
}
.auth-title{margin-bottom:.42rem;color:#17132B!important;font-size:1.95rem;font-weight:800;letter-spacing:-.035em;}
.auth-description{margin-bottom:1.2rem;color:#625C76!important;font-size:.96rem;line-height:1.55;}
label[data-testid="stWidgetLabel"] p{color:#2F2942!important;font-weight:650!important;}
div[data-baseweb="input"]>div{min-height:48px;border-radius:14px!important;background:rgba(250,250,255,.96)!important;}
.stButton>button,.stFormSubmitButton>button{min-height:48px;border-radius:14px!important;font-weight:750!important;}
.stFormSubmitButton>button[kind="primary"]{
 border:none!important;color:#fff!important;
 background:linear-gradient(135deg,#7C3AED,#4F46E5 55%,#2563EB)!important;
}
.stButton>button:not([kind="primary"]){background:#FAF9FF!important;color:#4C1D95!important;border:1px solid #DDD6FE!important;}
div[data-testid="stCaptionContainer"],div[data-testid="stCaptionContainer"] p{color:#5B5674!important;}
.verify-center{text-align:center;}
.verify-icon{
 width:68px;height:68px;margin:0 auto 1rem auto;display:flex;align-items:center;justify-content:center;
 border-radius:22px;font-size:1.85rem;color:#4F46E5!important;background:linear-gradient(135deg,#DBEAFE,#F3E8FF);
}
div[data-testid="stAlert"]{border-radius:14px;}
.footer-features{margin-top:1.35rem;text-align:center;color:#6B647D!important;font-size:.84rem;}
.footer-security{margin-top:.35rem;text-align:center;color:#8E879F!important;font-size:.75rem;}
</style>
""",
        unsafe_allow_html=True,
    )

    raw_html("""
    <div class="brand-wrapper">
      <div class="brand-logo">IL</div>
      <h1 class="brand-title">IntelliLearn</h1>
      <div class="brand-subtitle">AI-Powered Personalized Learning &amp; Document Intelligence</div>
      <div class="brand-small">Upload → Understand → Practice → Improve</div>
    </div>
    """)

    _, auth_col, _ = st.columns([1.1, 1.35, 1.1])

    with auth_col:
        with st.container(border=True):

            if st.session_state.auth_view == "signin":
                raw_html("""
                <div class="auth-badge">Student Portal</div>
                <div class="auth-title">Welcome back</div>
                <div class="auth-description">Sign in to continue to your personalized learning workspace.</div>
                """)

                if st.session_state.pop("password_reset_success", False):
                    st.success("Password changed successfully. Sign in with your new password.")

                with st.form("signin_form"):
                    identifier = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)

                if submit:
                    if not identifier.strip() or not password:
                        st.error("Please enter your username and password.")
                    else:
                        try:
                            sign_in_with_username(identifier, password)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Sign in failed: {exc}")

                if st.button("Forgot password?", use_container_width=True):
                    st.session_state.auth_view = "forgot_password"
                    st.rerun()

                st.divider()
                st.caption("New to IntelliLearn?")

                if st.button("Create a new account", use_container_width=True):
                    st.session_state.auth_view = "register"
                    st.rerun()

            elif st.session_state.auth_view == "forgot_password":
                raw_html("""
                <div class="auth-badge">Account Recovery</div>
                <div class="auth-title">Forgot your password?</div>
                <div class="auth-description">Enter your registered email address and we will send you a secure reset-password link.</div>
                """)

                if st.session_state.pop("recovery_error", False):
                    st.error("That reset link is invalid or expired. Please request a new one.")

                with st.form("forgot_form"):
                    email = st.text_input("Registered email address", placeholder="you@example.com")
                    submit = st.form_submit_button("Send reset password link", type="primary", use_container_width=True)

                if submit:
                    email = email.strip().lower()
                    if not email or "@" not in email or "." not in email.split("@")[-1]:
                        st.error("Please enter a valid email address.")
                    else:
                        try:
                            send_password_reset_email(email, PASSWORD_RESET_REDIRECT_URL)
                            st.success(
                                "If an IntelliLearn account exists for that email, "
                                "a reset link has been sent. Check your inbox and spam folder."
                            )
                        except Exception as exc:
                            st.error(f"Could not send reset email: {exc}")

                st.divider()
                if st.button("Back to sign in", use_container_width=True):
                    st.session_state.auth_view = "signin"
                    st.rerun()

            elif st.session_state.auth_view == "reset_password":
                if not st.session_state.get("recovery_verified"):
                    st.session_state.auth_view = "forgot_password"
                    st.rerun()

                raw_html("""
                <div class="verify-center">
                  <div class="verify-icon">🔐</div>
                  <div class="auth-badge">Password Recovery</div>
                  <div class="auth-title">Create a new password</div>
                  <div class="auth-description">Your recovery link is verified. Choose a new password for your account.</div>
                </div>
                """)

                with st.form("reset_form"):
                    password = st.text_input("New password", type="password", placeholder="Minimum 8 characters")
                    confirm = st.text_input("Confirm new password", type="password", placeholder="Re-enter your new password")
                    submit = st.form_submit_button("Reset password", type="primary", use_container_width=True)

                if submit:
                    if len(password) < 8:
                        st.error("Password must contain at least 8 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            update_recovery_password(password)
                            st.session_state.pop("recovery_verified", None)
                            st.session_state.password_reset_success = True
                            st.session_state.auth_view = "signin"
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not update password: {exc}")

            elif st.session_state.auth_view == "register":
                raw_html("""
                <div class="auth-badge">Get Started</div>
                <div class="auth-title">Create your account</div>
                <div class="auth-description">Create your student profile and verify your email to start using IntelliLearn.</div>
                """)

                with st.form("register_form"):
                    full_name = st.text_input("Full name", placeholder="Enter your full name")
                    username = st.text_input("Username", placeholder="Choose a unique username")
                    email = st.text_input("Email address", placeholder="you@example.com")
                    password = st.text_input("Create password", type="password", placeholder="Minimum 8 characters")
                    confirm = st.text_input("Confirm password", type="password", placeholder="Re-enter your password")
                    submit = st.form_submit_button("Create account", type="primary", use_container_width=True)

                if submit:
                    if not all([full_name.strip(), username.strip(), email.strip(), password, confirm]):
                        st.error("Please complete every field.")
                    elif not valid_username(username):
                        st.error("Username must be 3–30 characters and contain only letters, numbers or underscores.")
                    elif "@" not in email or "." not in email.split("@")[-1]:
                        st.error("Please enter a valid email address.")
                    elif len(password) < 8:
                        st.error("Password must contain at least 8 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            email = email.strip().lower()
                            sign_up(full_name.strip(), username.strip(), email, password)
                            st.session_state.pending_verification_email = email
                            st.session_state.verification_sent_at = time.time()
                            st.session_state.auth_view = "verify"
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Registration failed: {exc}")

                st.divider()
                if st.button("Back to sign in", use_container_width=True):
                    st.session_state.auth_view = "signin"
                    st.rerun()

            elif st.session_state.auth_view == "verify":
                email = st.session_state.get("pending_verification_email", "")

                if not email:
                    st.session_state.auth_view = "register"
                    st.rerun()

                raw_html("""
                <div class="verify-center">
                  <div class="verify-icon">✉</div>
                  <div class="auth-badge">Email Verification</div>
                  <div class="auth-title">Check your inbox</div>
                  <div class="auth-description">Enter the latest verification code sent to your email.</div>
                </div>
                """)

                st.info(f"Verification code sent to **{email}**")

                with st.form("verify_form"):
                    code = st.text_input("Verification code", placeholder="Enter the latest verification code")
                    submit = st.form_submit_button("Verify email", type="primary", use_container_width=True)

                if submit:
                    if not code.strip():
                        st.error("Please enter the verification code.")
                    else:
                        try:
                            verify_signup_otp(email, code.strip())
                            st.session_state.pop("pending_verification_email", None)
                            st.session_state.pop("verification_sent_at", None)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Verification failed: {exc}")

                st.caption("Didn't receive the email or has the code expired?")

                if st.button("Resend verification code", use_container_width=True):
                    last_sent = float(st.session_state.get("verification_sent_at", 0))
                    remaining = RESEND_COOLDOWN_SECONDS - (time.time() - last_sent)

                    if last_sent and remaining > 0:
                        st.info(f"Please wait {int(remaining) + 1} seconds before requesting another code.")
                    else:
                        try:
                            resend_signup_otp(email)
                            st.session_state.verification_sent_at = time.time()
                            st.success("A new verification code has been sent. Use the newest code.")
                        except Exception as exc:
                            st.error(f"Could not resend verification code: {exc}")

                st.divider()
                if st.button("Back to sign in", use_container_width=True):
                    st.session_state.auth_view = "signin"
                    st.rerun()

    raw_html("""
    <div class="footer-features">RAG Document Q&amp;A · AI Quizzes · Flashcards · Study Planning · Learning Analytics</div>
    <div class="footer-security">Secure authentication powered by Supabase</div>
    """)


login_page = st.Page(auth_page, title="IntelliLearn", icon="🎓", url_path="login")
dashboard_page = st.Page("pages/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:", url_path="dashboard")
syllabus_page = st.Page("pages/2_My_Syllabus.py", title="My Syllabus", icon=":material/menu_book:", url_path="syllabus")
documents_page = st.Page("pages/2_My_Documents.py", title="My Documents", icon=":material/folder:", url_path="documents")
ask_page = st.Page("pages/3_Ask_IntelliLearn.py", title="Ask IntelliLearn", icon=":material/smart_toy:", url_path="ask")
quiz_page = st.Page("pages/4_Quiz.py", title="Quiz", icon=":material/quiz:", url_path="quiz")
flashcards_page = st.Page("pages/5_Flashcards.py", title="Flashcards", icon=":material/style:", url_path="flashcards")
study_plan_page = st.Page("pages/6_Study_Plan.py", title="Study Plan", icon=":material/calendar_month:", url_path="study-plan")
progress_page = st.Page("pages/7_Progress.py", title="Progress", icon=":material/monitoring:", url_path="progress")

if is_logged_in():
    pages = [
        dashboard_page,
        syllabus_page,
        documents_page,
        ask_page,
        quiz_page,
        flashcards_page,
        study_plan_page,
        progress_page,
    ]
else:
    pages = [login_page]

st.navigation(pages, position="hidden").run()
