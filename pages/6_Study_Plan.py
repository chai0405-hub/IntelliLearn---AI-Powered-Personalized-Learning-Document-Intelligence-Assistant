from datetime import date, timedelta
import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.db import (
    get_quiz_attempts,
    list_curricula,
    list_curriculum_questions,
    list_curriculum_topics,
    list_curriculum_units,
    save_study_plan,
)
from utils.gemini_client import generate_text


st.set_page_config(
    page_title="Study Plan | IntelliLearn",
    page_icon="📅",
    layout="wide",
)
require_auth()
render_sidebar()

st.title("Personalized Study Planner")
st.caption("Build a realistic plan using quiz performance and, when available, your uploaded curriculum map.")

attempts = get_quiz_attempts()
weak_summary = "No quiz data is available yet."
if attempts:
    latest_by_topic = {}
    for item in attempts:
        latest_by_topic[item["topic"]] = float(item["percentage"])
    sorted_topics = sorted(latest_by_topic.items(), key=lambda x: x[1])
    weak_summary = ", ".join(
        f"{topic}: {score:.0f}%" for topic, score in sorted_topics[:5]
    )

curricula = list_curricula()
curriculum_map = {
    "Manual topics only": None,
    **{
        f"{c['subject_name']}" + (f" · {c['semester']}" if c.get("semester") else ""): c
        for c in curricula
    },
}

selected_curriculum_label = st.selectbox(
    "Curriculum (optional)",
    list(curriculum_map.keys()),
)
selected_curriculum = curriculum_map[selected_curriculum_label]

curriculum_summary = "No uploaded curriculum selected."
if selected_curriculum:
    units = list_curriculum_units(selected_curriculum["id"])
    topics = list_curriculum_topics(selected_curriculum["id"])
    questions = list_curriculum_questions(selected_curriculum["id"], limit=200)

    topics_by_unit = {}
    for topic in topics:
        topics_by_unit.setdefault(topic["unit_id"], []).append(topic["topic_name"])

    lines = []
    for unit in units:
        label = f"{unit.get('unit_number') or ''} {unit.get('unit_title') or ''}".strip()
        unit_topics = topics_by_unit.get(unit["id"], [])
        qb_count = sum(1 for q in questions if q.get("unit_id") == unit["id"])
        lines.append(
            f"- {label}: {', '.join(unit_topics) if unit_topics else 'No extracted topics'} "
            f"(mapped question-bank questions: {qb_count})"
        )
    curriculum_summary = "\n".join(lines)

with st.form("study_plan"):
    exam_date = st.date_input(
        "Exam date",
        value=date.today() + timedelta(days=30),
        min_value=date.today() + timedelta(days=1),
    )
    daily_minutes = st.slider("Daily study time (minutes)", 30, 300, 120, step=15)
    subjects_text = st.text_area(
        "Additional subjects / topics (optional)",
        placeholder="DBMS, Operating Systems, revision topics...",
    )
    submitted = st.form_submit_button("Generate Study Plan", type="primary")

if submitted:
    subjects = [x.strip() for x in subjects_text.split(",") if x.strip()]
    if selected_curriculum:
        subjects.insert(0, selected_curriculum["subject_name"])

    if not subjects:
        st.error("Select a curriculum or enter at least one subject/topic.")
    else:
        try:
            days_left = (exam_date - date.today()).days
            prompt = f"""
You are IntelliLearn's student study-planning assistant.

Create a practical study plan in Markdown.

Days until exam: {days_left}
Daily study time: {daily_minutes} minutes
Subjects/topics: {', '.join(subjects)}

RECENT QUIZ PERFORMANCE / WEAK AREAS:
{weak_summary}

CURRICULUM MAP:
{curriculum_summary}

Requirements:
- Prioritize weaker quiz topics where relevant.
- If a curriculum map is present, cover its units/topics systematically.
- Give extra attention to units with more mapped question-bank questions, but do not ignore other units.
- Keep the workload within {daily_minutes} minutes per day.
- Include revision, active recall and practice quizzes.
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
