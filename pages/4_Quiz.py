import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.ui import apply_app_style, page_navigation
from utils.db import (
    list_curricula,
    list_curriculum_questions,
    list_curriculum_topics,
    list_curriculum_units,
    list_documents,
    save_quiz_attempt,
)
from utils.rag import retrieve, retrieve_curriculum_materials
from utils.gemini_client import generate_json


st.set_page_config(
    page_title="Quiz | IntelliLearn",
    page_icon="📝",
    layout="wide",
)
require_auth()
apply_app_style()
render_sidebar()

st.title("AI Quiz Generator")
st.caption(
    "Generate document-grounded MCQs from a selected PDF or from an entire syllabus unit using your attached study materials."
)
page_navigation("quiz")

documents = list_documents()
curricula = list_curricula()

if not documents:
    st.info("Upload a textbook or notes PDF first.")
    st.stop()

source_mode = st.radio(
    "Quiz source",
    ["Document Only", "Syllabus Unit"],
    horizontal=True,
)

question_count = 5
difficulty = "Medium"
context = ""
quiz_topic = "Quiz"
source_description = ""

if source_mode == "Document Only":
    doc_map = {doc["filename"]: doc for doc in documents}

    with st.form("quiz_document_setup"):
        selected_name = st.selectbox("Document", list(doc_map.keys()))
        topic = st.text_input("Topic", placeholder="Example: Supervised Learning")
        question_count = st.slider("Number of questions", 3, 10, 5)
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
        make_quiz = st.form_submit_button("Generate Quiz", type="primary")

    if make_quiz:
        if not topic.strip():
            st.error("Enter a topic.")
        else:
            try:
                doc = doc_map[selected_name]
                chunks = retrieve(doc["id"], topic.strip(), match_count=10)
                if not chunks:
                    raise ValueError("No relevant passages were found in this document.")

                context = "\n\n".join(
                    f"[FILE: {selected_name} | PAGE: {x['page_number']}]\n{x['content']}"
                    for x in chunks
                )
                quiz_topic = topic.strip()
                source_description = f"Document: {selected_name}"

                prompt = f"""
Create exactly {question_count} multiple-choice questions for a student.

Topic: {quiz_topic}
Difficulty: {difficulty}
Source: {source_description}

Use ONLY this uploaded-document context:
{context}

Return JSON only as an array with this exact structure:
[
  {{
    "question": "Question text",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A",
    "explanation": "Short explanation grounded in the uploaded document",
    "source_file": "{selected_name}",
    "page": 12
  }}
]

Rules:
- Exactly four options.
- answer must be A, B, C, or D.
- Do not use facts outside the supplied context.
- source_file and page must correspond to the supplied context.
- If the context cannot support exactly {question_count} reliable questions, return fewer questions rather than inventing facts.
"""
                quiz = generate_json(prompt)
                if not isinstance(quiz, list) or not quiz:
                    raise ValueError("The AI could not generate a reliable quiz from the retrieved material.")

                st.session_state.generated_quiz = quiz
                st.session_state.generated_quiz_topic = quiz_topic
                st.session_state.generated_quiz_source = source_description
                st.success(f"Generated {len(quiz)} grounded question(s).")

            except Exception as exc:
                st.error(f"Quiz generation failed: {exc}")

else:
    if not curricula:
        st.warning("Create a curriculum in My Syllabus before using syllabus-unit quizzes.")
        st.stop()

    curriculum_labels = {
        f"{c['subject_name']}" + (f" · {c['semester']}" if c.get("semester") else ""): c
        for c in curricula
    }

    selected_curriculum_label = st.selectbox("Curriculum", list(curriculum_labels.keys()))
    selected_curriculum = curriculum_labels[selected_curriculum_label]
    units = list_curriculum_units(selected_curriculum["id"])

    if not units:
        st.warning("No units were extracted for this curriculum.")
        st.stop()

    unit_labels = {
        f"{u.get('unit_number') or ''} {u.get('unit_title') or ''}".strip(): u
        for u in units
    }

    with st.form("quiz_curriculum_setup"):
        selected_unit_label = st.selectbox("Unit / Module", list(unit_labels.keys()))
        question_count = st.slider("Number of questions", 3, 10, 5, key="curr_q_count")
        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
            key="curr_q_difficulty",
        )
        make_quiz = st.form_submit_button("Generate Unit Quiz", type="primary")

    if make_quiz:
        try:
            unit = unit_labels[selected_unit_label]
            topics = list_curriculum_topics(selected_curriculum["id"], unit_id=unit["id"])
            topic_names = [t["topic_name"] for t in topics]
            query = f"{selected_unit_label}. " + "; ".join(topic_names)

            chunks = retrieve_curriculum_materials(
                selected_curriculum["id"],
                query,
                match_count=14,
            )

            if not chunks:
                raise ValueError(
                    "No textbook/notes passages were found for this curriculum. Attach study material in My Documents first."
                )

            context = "\n\n".join(
                f"[FILE: {x.get('filename', 'Uploaded document')} | PAGE: {x['page_number']}]\n{x['content']}"
                for x in chunks
            )

            qb_questions = list_curriculum_questions(
                selected_curriculum["id"],
                unit_id=unit["id"],
                limit=12,
            )
            question_style = "\n".join(
                f"- {q['question_text']}" for q in qb_questions[:12]
            ) or "[No mapped question-bank questions available]"

            quiz_topic = f"{selected_curriculum['subject_name']} — {selected_unit_label}"
            source_description = "Syllabus unit + attached study materials"

            prompt = f"""
Create up to {question_count} multiple-choice questions for the syllabus unit below.

Subject: {selected_curriculum['subject_name']}
Unit/Module: {selected_unit_label}
Topics: {', '.join(topic_names) if topic_names else 'No explicit topic list'}
Difficulty: {difficulty}

QUESTION-BANK STYLE HINTS:
{question_style}

Important: question-bank items are style/priority hints only. The factual content of every generated question,
option, correct answer and explanation MUST be supported by the uploaded study-material context below.

UPLOADED STUDY-MATERIAL CONTEXT:
{context}

Return JSON only:
[
  {{
    "question": "Question text",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A",
    "explanation": "Short grounded explanation",
    "source_file": "Exact filename shown in context",
    "page": 12
  }}
]

Rules:
- Exactly four options per question.
- answer must be A, B, C, or D.
- Never introduce facts that are not present in the uploaded study-material context.
- source_file and page must be traceable to the supplied context.
- If only 3 reliable questions can be supported, return 3 rather than inventing the rest.
"""
            quiz = generate_json(prompt)
            if not isinstance(quiz, list) or not quiz:
                raise ValueError("The available study material was not sufficient for a reliable unit quiz.")

            st.session_state.generated_quiz = quiz
            st.session_state.generated_quiz_topic = quiz_topic
            st.session_state.generated_quiz_source = source_description
            st.success(f"Generated {len(quiz)} grounded question(s) for {selected_unit_label}.")

        except Exception as exc:
            st.error(f"Quiz generation failed: {exc}")


quiz = st.session_state.get("generated_quiz")

if quiz:
    st.divider()
    st.caption(st.session_state.get("generated_quiz_source", ""))

    with st.form("take_quiz"):
        answers = []
        for idx, item in enumerate(quiz, start=1):
            st.markdown(f"### {idx}. {item['question']}")
            option_keys = ["A", "B", "C", "D"]
            selected = st.radio(
                "Choose one",
                option_keys,
                format_func=lambda k, item=item: f"{k}. {item['options'][k]}",
                key=f"q_{idx}",
                index=None,
            )
            answers.append(selected)

        submitted = st.form_submit_button("Submit Quiz", type="primary")

    if submitted:
        if any(answer is None for answer in answers):
            st.error("Please answer every question.")
        else:
            score = sum(
                1 for selected, item in zip(answers, quiz)
                if selected == item["answer"]
            )
            total = len(quiz)
            percentage = round(score / total * 100, 1)

            save_quiz_attempt(
                st.session_state.get("generated_quiz_topic", "Quiz"),
                score,
                total,
            )

            st.success(f"Score: {score}/{total} ({percentage}%)")

            for idx, (selected, item) in enumerate(zip(answers, quiz), start=1):
                correct = selected == item["answer"]
                with st.expander(
                    f"Question {idx} — {'Correct' if correct else 'Review'}"
                ):
                    st.write(f"Your answer: {selected}")
                    st.write(f"Correct answer: {item['answer']}")
                    st.write(item.get("explanation", ""))
                    st.caption(
                        f"Source: {item.get('source_file', 'Uploaded material')} · "
                        f"Page {item.get('page', 'N/A')}"
                    )
