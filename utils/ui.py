import streamlit as st


PAGE_FLOW = {
    "dashboard": {
        "step": 1,
        "previous": None,
        "next": ("My Syllabus", "pages/2_My_Syllabus.py"),
    },
    "syllabus": {
        "step": 2,
        "previous": ("Dashboard", "pages/1_Dashboard.py"),
        "next": ("My Documents", "pages/2_My_Documents.py"),
    },
    "documents": {
        "step": 3,
        "previous": ("My Syllabus", "pages/2_My_Syllabus.py"),
        "next": ("Ask IntelliLearn", "pages/3_Ask_IntelliLearn.py"),
    },
    "ask": {
        "step": 4,
        "previous": ("My Documents", "pages/2_My_Documents.py"),
        "next": ("Quiz", "pages/4_Quiz.py"),
    },
    "quiz": {
        "step": 5,
        "previous": ("Ask IntelliLearn", "pages/3_Ask_IntelliLearn.py"),
        "next": ("Flashcards", "pages/5_Flashcards.py"),
    },
    "flashcards": {
        "step": 6,
        "previous": ("Quiz", "pages/4_Quiz.py"),
        "next": ("Study Plan", "pages/6_Study_Plan.py"),
    },
    "study_plan": {
        "step": 7,
        "previous": ("Flashcards", "pages/5_Flashcards.py"),
        "next": ("Progress", "pages/7_Progress.py"),
    },
    "progress": {
        "step": 8,
        "previous": ("Study Plan", "pages/6_Study_Plan.py"),
        "next": ("Dashboard", "pages/1_Dashboard.py"),
    },
}


def apply_app_style() -> None:
    """Apply a consistent post-login IntelliLearn visual system."""
    st.markdown(
        """
        <style>
        :root {
            --il-bg: #090b14;
            --il-panel: rgba(20, 23, 39, 0.82);
            --il-panel-2: rgba(28, 31, 50, 0.72);
            --il-border: rgba(160, 174, 255, 0.14);
            --il-text: #f8fafc;
            --il-muted: #aeb7cc;
            --il-purple: #7c3aed;
            --il-indigo: #4f46e5;
            --il-blue: #2563eb;
        }

        /* Main app background */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background:
                radial-gradient(circle at 88% 10%, rgba(79, 70, 229, 0.20), transparent 30%),
                radial-gradient(circle at 14% 80%, rgba(124, 58, 237, 0.14), transparent 32%),
                radial-gradient(circle at 70% 75%, rgba(37, 99, 235, 0.08), transparent 28%),
                linear-gradient(145deg, #090b14 0%, #0d101b 48%, #0a0c15 100%) !important;
            color: var(--il-text) !important;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1280px;
            padding-top: 2.1rem;
            padding-bottom: 4rem;
        }

        /* Typography */
        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stCaptionContainer"],
        label[data-testid="stWidgetLabel"] p {
            color: var(--il-text);
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: var(--il-muted) !important;
        }

        h1 {
            letter-spacing: -0.045em !important;
            font-weight: 820 !important;
        }

        h2, h3 {
            letter-spacing: -0.025em !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 20% 4%, rgba(124, 58, 237, 0.16), transparent 25%),
                linear-gradient(180deg, #171a2a 0%, #141725 55%, #11131f 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-top: 1.8rem;
        }

        section[data-testid="stSidebar"] h2 {
            color: #ffffff !important;
            font-size: 1.55rem !important;
            font-weight: 850 !important;
            letter-spacing: -0.04em !important;
            margin-bottom: 0.8rem !important;
        }

        section[data-testid="stSidebar"] [data-testid="stPageLink"] {
            border-radius: 13px !important;
            padding: 0.15rem 0.25rem !important;
            margin-bottom: 0.24rem !important;
            transition: all 0.16s ease;
        }

        section[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
            background: rgba(124, 58, 237, 0.15) !important;
            transform: translateX(2px);
        }

        section[data-testid="stSidebar"] [data-testid="stPageLink"] p,
        section[data-testid="stSidebar"] [data-testid="stPageLink"] span {
            color: #f4f6fb !important;
            font-weight: 610 !important;
        }

        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.10) !important;
        }

        /* Cards / bordered containers */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(145deg, rgba(23, 27, 44, 0.90), rgba(15, 18, 31, 0.86)) !important;
            border: 1px solid var(--il-border) !important;
            border-radius: 20px !important;
            box-shadow: 0 16px 40px rgba(0,0,0,0.18) !important;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(29, 33, 54, 0.86), rgba(18, 21, 36, 0.82));
            border: 1px solid rgba(140, 150, 235, 0.15);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            box-shadow: 0 12px 28px rgba(0,0,0,0.14);
        }

        [data-testid="stMetricLabel"] p {
            color: #b8c0d4 !important;
            font-weight: 650 !important;
        }

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        /* Buttons */
        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {
            min-height: 44px;
            border-radius: 13px !important;
            border: 1px solid rgba(143, 155, 235, 0.20) !important;
            color: #f8fafc !important;
            background: linear-gradient(145deg, rgba(34, 39, 62, .92), rgba(23, 27, 44, .95)) !important;
            font-weight: 700 !important;
            transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(124, 58, 237, 0.60) !important;
            box-shadow: 0 10px 22px rgba(69, 55, 180, 0.18);
        }

        .stFormSubmitButton > button[kind="primary"],
        .stButton > button[kind="primary"] {
            border: none !important;
            background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 58%, #2563eb 100%) !important;
            box-shadow: 0 11px 26px rgba(79, 70, 229, 0.28) !important;
        }

        /* Inputs */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea {
            background: rgba(17, 20, 34, 0.92) !important;
            border-color: rgba(139, 149, 220, 0.16) !important;
            border-radius: 13px !important;
            color: #f8fafc !important;
        }

        input, textarea {
            color: #f8fafc !important;
        }

        /* Tabs / radio / expanders */
        [data-testid="stExpander"] {
            background: rgba(20, 23, 39, 0.60) !important;
            border: 1px solid rgba(139,149,220,0.12) !important;
            border-radius: 16px !important;
        }

        [data-testid="stAlert"] {
            border-radius: 14px !important;
        }

        hr {
            border-color: rgba(153, 164, 225, 0.12) !important;
        }

        /* Page navigation bar */
        .il-step-pill {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .36rem .72rem;
            border-radius: 999px;
            color: #c9d1e6;
            font-size: .78rem;
            font-weight: 700;
            border: 1px solid rgba(137, 147, 222, .18);
            background: rgba(22, 26, 43, .72);
        }

        .il-step-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: linear-gradient(135deg, #8b5cf6, #3b82f6);
            box-shadow: 0 0 14px rgba(99, 102, 241, .7);
        }

        /* Sidebar sign out */
        section[data-testid="stSidebar"] .stButton > button {
            background: rgba(255,255,255,0.035) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
        }

        @media (max-width: 900px) {
            [data-testid="stMainBlockContainer"] {
                padding-top: 1.35rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_navigation(current_page: str) -> None:
    """Render a compact previous/next workflow navigator on every logged-in page."""
    info = PAGE_FLOW[current_page]
    total = len(PAGE_FLOW)
    previous_page = info["previous"]
    next_page = info["next"]

    left, middle, right = st.columns([1.6, 1, 1.6])

    with left:
        if previous_page:
            if st.button(
                f"← Back: {previous_page[0]}",
                key=f"nav_back_{current_page}",
                use_container_width=True,
            ):
                st.switch_page(previous_page[1])
        else:
            st.markdown("&nbsp;", unsafe_allow_html=True)

    with middle:
        st.markdown(
            f"""
            <div style="text-align:center;padding-top:.35rem;">
                <span class="il-step-pill">
                    <span class="il-step-dot"></span>
                    Step {info['step']} of {total}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        if st.button(
            f"Next: {next_page[0]} →",
            key=f"nav_next_{current_page}",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page(next_page[1])

    st.markdown("<div style='height:.45rem'></div>", unsafe_allow_html=True)
