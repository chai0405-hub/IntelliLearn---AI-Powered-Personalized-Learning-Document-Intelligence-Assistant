from datetime import date, timedelta
import streamlit as st
from utils.auth import require_auth, render_sidebar
from utils.db import get_quiz_attempts, save_study_plan
from utils.gemini_client import generate_text

st.set_page_config(page_title="Study Plan | IntelliLearn", page_icon="📅", layout="wide")
require_auth()
render_sidebar()

st.title("Personalized Study Planner")

attempts = get_quiz_attempts()
weak_summary = "No quiz data is available yet."
if attempts:
    latest_by_topic = {}
    for item in attempts:
        latest_by_topic[item["topic"]] = float(item["percentage"])
    sorted_topics = sorted(latest_by_topic.items(), key=lambda x: x[1])
    weak_summary = ", ".join(f"{topic}: {score:.0f}%" for topic, score in sorted_topics[:5])

with st.form("study_plan"):
    exam_date = st.date_input(
        "Exam date",
        value=date.today() + timedelta(days=30),
        min_value=date.today() + timedelta(days=1),
    )
    daily_minutes = st.slider("Daily study time (minutes)", 30, 300, 120, step=15)
    subjects_text = st.text_area(
        "Subjects / topics",
        placeholder="Machine Learning, DBMS, Operating Systems",
    )
    submitted = st.form_submit_button("Generate Study Plan", type="primary")

if submitted:
    subjects = [x.strip() for x in subjects_text.split(",") if x.strip()]
    if not subjects:
        st.error("Enter at least one subject or topic.")
    else:
        try:
            days_left = (exam_date - date.today()).days
            prompt = f"""
You are a student study-planning assistant.

Create a practical study plan in Markdown.

Days until exam: {days_left}
Daily study time: {daily_minutes} minutes
Subjects/topics: {", ".join(subjects)}

Recent quiz performance / weak areas:
{weak_summary}

Requirements:
- Prioritize weaker topics where relevant.
- Include daily or weekly blocks.
- Include revision and practice quizzes.
- Keep the workload within {daily_minutes} minutes per day.
- Include a final revision phase before the exam.
- Make the plan realistic for a college student.
"""
            plan = generate_text(prompt)
            save_study_plan(exam_date, daily_minutes, subjects, plan)
            st.session_state.latest_study_plan = plan
        except Exception as exc:
            st.error(f"Could not generate plan: {exc}")

plan = st.session_state.get("latest_study_plan")
if plan:
    st.divider()
    st.markdown(plan)
