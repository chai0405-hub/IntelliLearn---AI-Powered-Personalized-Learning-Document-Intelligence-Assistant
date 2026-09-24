import streamlit as st
from utils.auth import require_auth, render_sidebar
from utils.db import list_documents
from utils.rag import retrieve
from utils.gemini_client import generate_json

st.set_page_config(page_title="Flashcards | IntelliLearn", page_icon="🧠", layout="wide")
require_auth()
render_sidebar()

st.title("AI Flashcards")

documents = list_documents()
if not documents:
    st.info("Upload a PDF first.")
    st.stop()

doc_map = {doc["filename"]: doc for doc in documents}

with st.form("flashcard_form"):
    selected_name = st.selectbox("Document", list(doc_map.keys()))
    topic = st.text_input("Topic", placeholder="Example: Classification")
    count = st.slider("Number of flashcards", 3, 12, 6)
    submitted = st.form_submit_button("Generate Flashcards", type="primary")

if submitted:
    if not topic.strip():
        st.error("Enter a topic.")
    else:
        try:
            chunks = retrieve(doc_map[selected_name]["id"], topic.strip(), match_count=8)
            context = "\n\n".join(
                f"[Page {x['page_number']}] {x['content']}" for x in chunks
            )

            prompt = f"""
Create {count} revision flashcards for the topic "{topic}" using ONLY the context below.

CONTEXT:
{context}

Return JSON only:
[
  {{
    "front": "Question or concept",
    "back": "Short student-friendly answer",
    "page": 12
  }}
]
"""
            cards = generate_json(prompt)
            st.session_state.flashcards = cards
        except Exception as exc:
            st.error(f"Could not generate flashcards: {exc}")

cards = st.session_state.get("flashcards", [])
if cards:
    st.divider()
    cols = st.columns(2)
    for idx, card in enumerate(cards):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{card['front']}**")
                with st.expander("Show answer"):
                    st.write(card["back"])
                    st.caption(f"Source page: {card.get('page', 'N/A')}")
