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
    "pages/1_Dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    url_path="dashboard",
    default=True,
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
