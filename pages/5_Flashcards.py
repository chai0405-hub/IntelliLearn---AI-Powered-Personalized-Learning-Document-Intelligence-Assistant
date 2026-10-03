import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.db import (
    list_curricula,
    list_curriculum_topics,
    list_curriculum_units,
    list_documents,
)
from utils.rag import retrieve, retrieve_curriculum_materials
from utils.gemini_client import generate_json


st.set_page_config(
    page_title="Flashcards | IntelliLearn",
    page_icon="🧠",
    layout="wide",
)
require_auth()
render_sidebar()

st.title("AI Flashcards")
st.caption("Generate revision cards from one PDF or from study materials linked to a syllabus unit.")

documents = list_documents()
curricula = list_curricula()

if not documents:
    st.info("Upload a PDF first.")
    st.stop()

source_mode = st.radio(
    "Flashcard source",
    ["Document Only", "Syllabus Unit"],
    horizontal=True,
)

if source_mode == "Document Only":
    doc_map = {doc["filename"]: doc for doc in documents}

    with st.form("flashcard_form_document"):
        selected_name = st.selectbox("Document", list(doc_map.keys()))
        topic = st.text_input("Topic", placeholder="Example: Classification")
        count = st.slider("Number of flashcards", 3, 12, 6)
        submitted = st.form_submit_button("Generate Flashcards", type="primary")

    if submitted:
        if not topic.strip():
            st.error("Enter a topic.")
        else:
            try:
                chunks = retrieve(doc_map[selected_name]["id"], topic.strip(), match_count=10)
                if not chunks:
                    raise ValueError("No relevant passages were found in this document.")

                context = "\n\n".join(
                    f"[FILE: {selected_name} | PAGE: {x['page_number']}] {x['content']}"
                    for x in chunks
                )

                prompt = f"""
Create up to {count} revision flashcards for the topic "{topic}" using ONLY the uploaded-document context below.

CONTEXT:
{context}

Return JSON only:
[
  {{
    "front": "Question or concept",
    "back": "Short student-friendly answer",
    "source_file": "{selected_name}",
    "page": 12
  }}
]

Do not add facts that are absent from the context. If fewer reliable cards can be made, return fewer cards.
"""
                cards = generate_json(prompt)
                st.session_state.flashcards = cards
            except Exception as exc:
                st.error(f"Could not generate flashcards: {exc}")

else:
    if not curricula:
        st.warning("Create a curriculum in My Syllabus first.")
        st.stop()

    curriculum_map = {
        f"{c['subject_name']}" + (f" · {c['semester']}" if c.get("semester") else ""): c
        for c in curricula
    }
    selected_curriculum_label = st.selectbox("Curriculum", list(curriculum_map.keys()))
    curriculum = curriculum_map[selected_curriculum_label]
    units = list_curriculum_units(curriculum["id"])

    if not units:
        st.warning("No units were extracted for this curriculum.")
        st.stop()

    unit_map = {
        f"{u.get('unit_number') or ''} {u.get('unit_title') or ''}".strip(): u
        for u in units
    }

    with st.form("flashcard_form_unit"):
        unit_label = st.selectbox("Unit / Module", list(unit_map.keys()))
        count = st.slider("Number of flashcards", 3, 12, 6, key="unit_flash_count")
        submitted = st.form_submit_button("Generate Unit Flashcards", type="primary")

    if submitted:
        try:
            unit = unit_map[unit_label]
            topics = list_curriculum_topics(curriculum["id"], unit_id=unit["id"])
            topic_names = [t["topic_name"] for t in topics]
            query = f"{unit_label}. " + "; ".join(topic_names)
            chunks = retrieve_curriculum_materials(curriculum["id"], query, match_count=14)

            if not chunks:
                raise ValueError("No attached study-material passages were found for this curriculum.")

            context = "\n\n".join(
                f"[FILE: {x.get('filename', 'Uploaded document')} | PAGE: {x['page_number']}] {x['content']}"
                for x in chunks
            )

            prompt = f"""
Create up to {count} revision flashcards for this syllabus unit using ONLY the attached study-material context.

Subject: {curriculum['subject_name']}
Unit/Module: {unit_label}
Topics: {', '.join(topic_names)}

CONTEXT:
{context}

Return JSON only:
[
  {{
    "front": "Question or concept",
    "back": "Short student-friendly answer",
    "source_file": "Exact filename shown in context",
    "page": 12
  }}
]

Do not add facts outside the context. Return fewer cards if the material cannot support all requested cards.
"""
            st.session_state.flashcards = generate_json(prompt)
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
                    st.caption(
                        f"Source: {card.get('source_file', 'Uploaded material')} · "
                        f"Page {card.get('page', 'N/A')}"
                    )
