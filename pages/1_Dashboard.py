import pandas as pd
import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.db import list_curricula, list_documents, get_quiz_attempts


st.set_page_config(
    page_title="Dashboard | IntelliLearn",
    page_icon="📊",
    layout="wide",
)
require_auth()
render_sidebar()

st.title(f"Welcome, {st.session_state.get('full_name', 'Student')}")
st.caption("Your personalized learning dashboard")

curricula = list_curricula()
documents = list_documents()
attempts = get_quiz_attempts()

average_score = (
    round(sum(float(x["percentage"]) for x in attempts) / len(attempts), 1)
    if attempts
    else 0
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Curricula", len(curricula))
c2.metric("Study PDFs", len(documents))
c3.metric("Quizzes", len(attempts))
c4.metric("Average score", f"{average_score}%")
c5.metric("Topics practiced", len(set(x["topic"] for x in attempts)) if attempts else 0)

st.divider()

left, right = st.columns([1.4, 1])

with left:
    st.subheader("Recent quiz performance")
    if attempts:
        df = pd.DataFrame(attempts)
        df["created_at"] = pd.to_datetime(df["created_at"])
        chart_df = df.set_index("created_at")[["percentage"]]
        st.line_chart(chart_df)
    else:
        st.info("Complete a quiz to see your progress chart.")

with right:
    st.subheader("Quick actions")
    if st.button("Set up Syllabus / Question Bank", use_container_width=True):
        st.switch_page("pages/2_My_Syllabus.py")
    if st.button("Upload Textbook / Notes", use_container_width=True):
        st.switch_page("pages/2_My_Documents.py")
    if st.button("Ask IntelliLearn", use_container_width=True):
        st.switch_page("pages/3_Ask_IntelliLearn.py")
    if st.button("Generate a Quiz", use_container_width=True):
        st.switch_page("pages/4_Quiz.py")
    if st.button("Create Study Plan", use_container_width=True):
        st.switch_page("pages/6_Study_Plan.py")

st.divider()
st.subheader("Recommended workflow")
st.markdown(
    """
1. **My Syllabus** → upload syllabus, question bank, or both.
2. **My Documents** → upload textbook/notes and attach them to the curriculum.
3. **Ask IntelliLearn** → get PDF-grounded answers first.
4. If the PDF is incomplete but the topic is in scope → use **Syllabus-Guided Recommended Answer**.
5. **Quiz / Study Plan / Progress** → practice and track learning.
"""
)
