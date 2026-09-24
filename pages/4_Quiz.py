import streamlit as st
from utils.auth import require_auth, render_sidebar
from utils.db import list_documents, save_quiz_attempt
from utils.rag import retrieve
from utils.gemini_client import generate_json

st.set_page_config(page_title="Quiz | IntelliLearn", page_icon="📝", layout="wide")
require_auth()
render_sidebar()

st.title("AI Quiz Generator")
st.caption("Generate MCQs from your uploaded study material.")

documents = list_documents()
if not documents:
    st.info("Upload a PDF first.")
    st.stop()

doc_map = {doc["filename"]: doc for doc in documents}

with st.form("quiz_setup"):
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
            chunks = retrieve(doc["id"], topic.strip(), match_count=8)
            context = "\n\n".join(
                f"[Page {x['page_number']}] {x['content']}" for x in chunks
            )

            prompt = f"""
Create exactly {question_count} multiple-choice questions for a student.

Topic: {topic}
Difficulty: {difficulty}

Use ONLY this document context:
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
    "explanation": "Short explanation grounded in the document",
    "page": 12
  }}
]

Rules:
- Exactly four options.
- answer must be A, B, C, or D.
- Do not use facts outside the context.
- page must be one of the cited context pages.
"""
            quiz = generate_json(prompt)
            if not isinstance(quiz, list):
                raise ValueError("The AI returned an unexpected quiz format.")
            st.session_state.generated_quiz = quiz
            st.session_state.generated_quiz_topic = topic.strip()
            st.success("Quiz generated.")
        except Exception as exc:
            st.error(f"Quiz generation failed: {exc}")

quiz = st.session_state.get("generated_quiz")

if quiz:
    st.divider()
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
            score = 0
            for selected, item in zip(answers, quiz):
                if selected == item["answer"]:
                    score += 1

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
                    st.write(item["explanation"])
                    st.caption(f"Source page: {item.get('page', 'N/A')}")
