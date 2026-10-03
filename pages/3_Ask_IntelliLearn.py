import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.ui import apply_app_style, page_navigation
from utils.db import list_curricula, list_documents
from utils.rag import answer_intelligently
from utils.curriculum import generate_syllabus_guided_answer


st.set_page_config(
    page_title="Ask IntelliLearn",
    page_icon="💬",
    layout="wide",
)
require_auth()
apply_app_style()
render_sidebar()

st.title("Ask IntelliLearn")
st.caption(
    "PDF-first answers with page sources. If the material is incomplete, IntelliLearn can offer a clearly labelled syllabus-guided answer."
)
page_navigation("ask")

documents = list_documents()
curricula = list_curricula()

if not documents:
    st.info("Upload a textbook or notes PDF first.")
    if st.button("Go to My Documents"):
        st.switch_page("pages/2_My_Documents.py")
    st.stop()

mode_label = st.radio(
    "Answer mode",
    ["Document Only", "All My Materials", "Syllabus-Aware"],
    horizontal=True,
    help=(
        "Document Only searches one PDF. All My Materials searches all PDFs attached to a curriculum. "
        "Syllabus-Aware additionally emphasizes curriculum mapping and fallback guidance."
    ),
)

mode = {
    "Document Only": "document",
    "All My Materials": "all_materials",
    "Syllabus-Aware": "syllabus_aware",
}[mode_label]

selected_doc = None
selected_curriculum = None

if mode == "document":
    doc_by_name = {doc["filename"]: doc for doc in documents}
    default_index = 0
    selected_id = st.session_state.get("selected_document_id")
    for idx, doc in enumerate(documents):
        if doc["id"] == selected_id:
            default_index = idx
            break

    selected_name = st.selectbox(
        "Selected PDF",
        [doc["filename"] for doc in documents],
        index=default_index,
    )
    selected_doc = doc_by_name[selected_name]
    st.session_state.selected_document_id = selected_doc["id"]

    if selected_doc.get("curriculum_id"):
        selected_curriculum = next(
            (c for c in curricula if c["id"] == selected_doc["curriculum_id"]),
            None,
        )
        if selected_curriculum:
            st.caption(
                f"Curriculum link: {selected_curriculum['subject_name']} — enables syllabus-guided fallback when needed."
            )
    else:
        st.caption("This PDF is not attached to a curriculum. Only document-grounded answers are available.")

else:
    if not curricula:
        st.warning("Create a syllabus/question-bank curriculum first for this answer mode.")
        if st.button("Go to My Syllabus"):
            st.switch_page("pages/2_My_Syllabus.py")
        st.stop()

    curr_label_map = {
        f"{c['subject_name']}" + (f" · {c['semester']}" if c.get("semester") else ""): c
        for c in curricula
    }
    labels = list(curr_label_map.keys())
    default_index = 0
    active_id = st.session_state.get("active_curriculum_id")
    for idx, label in enumerate(labels):
        if curr_label_map[label]["id"] == active_id:
            default_index = idx
            break

    selected_label = st.selectbox("Curriculum", labels, index=default_index)
    selected_curriculum = curr_label_map[selected_label]
    st.session_state.active_curriculum_id = selected_curriculum["id"]

    attached_docs = [d for d in documents if d.get("curriculum_id") == selected_curriculum["id"]]
    if not attached_docs:
        st.warning(
            "No textbook/notes are attached to this curriculum yet. Upload study material and attach it before asking questions."
        )
        if st.button("Upload Study Material"):
            st.switch_page("pages/2_My_Documents.py")
        st.stop()

    st.caption(
        f"Searching {len(attached_docs)} attached study material(s) for {selected_curriculum['subject_name']}."
    )


scope_id = (
    selected_doc["id"]
    if selected_doc
    else selected_curriculum["id"]
    if selected_curriculum
    else "none"
)
chat_key = f"intellilearn_chat_{mode}_{scope_id}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []


def render_mapping(match: dict | None):
    if not match:
        return
    similarity = float(match.get("similarity") or 0)
    official = "Official syllabus" if match.get("is_official") else "Question-bank / inferred"
    unit = f"{match.get('unit_number') or ''} {match.get('unit_title') or ''}".strip()
    cols = st.columns([1.5, 1.5, 1])
    cols[0].caption(f"**Unit/Module:** {unit or 'Not specified'}")
    cols[1].caption(f"**Topic:** {match.get('topic_name') or '—'}")
    cols[2].caption(f"**Match:** {similarity:.0%} · {official}")


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander("Sources"):
        for source in sources[:10]:
            filename = source.get("filename") or (selected_doc.get("filename") if selected_doc else "Uploaded document")
            similarity = float(source.get("similarity") or 0)
            st.write(
                f"{filename} — Page {source.get('page_number', 'N/A')} "
                f"(similarity {similarity:.2f})"
            )


messages = st.session_state[chat_key]
for idx, message in enumerate(messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
            continue

        result = message.get("result", {})
        status = result.get("status")
        match = result.get("curriculum_match")

        if status == "grounded_answer":
            st.success("Answer found in your uploaded study material.")
            st.markdown(result.get("answer") or "")
            render_mapping(match)
            render_sources(result.get("sources") or [])

        elif status == "syllabus_fallback":
            st.warning(
                "Sufficient information was not found in the uploaded study material, "
                "but this question matches your curriculum."
            )
            render_mapping(match)
            render_sources(result.get("sources") or [])

            recommended = message.get("recommended_answer")
            if recommended:
                st.info("Recommended AI Answer — Syllabus-Guided, not taken from the uploaded PDF")
                st.markdown(recommended)
            else:
                if st.button(
                    "Generate Recommended Answer",
                    type="primary",
                    key=f"fallback_{chat_key}_{idx}",
                ):
                    try:
                        with st.spinner("Generating a syllabus-guided recommendation..."):
                            message["recommended_answer"] = generate_syllabus_guided_answer(
                                message.get("question", ""),
                                match,
                            )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not generate the recommended answer: {exc}")

        else:
            st.warning(
                "I could not find enough information in the uploaded material, and the question did not match the curriculum strongly enough for a syllabus-guided answer."
            )
            render_mapping(match)
            if mode == "document" and not selected_doc.get("curriculum_id"):
                st.caption("Tip: attach this document to a syllabus/question-bank curriculum to enable syllabus-aware fallback.")


question = st.chat_input("Ask a question from your learning material...")

if question:
    messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching your materials and checking curriculum coverage..."):
            try:
                result = answer_intelligently(
                    question=question,
                    mode=mode,
                    document_id=selected_doc["id"] if selected_doc else None,
                    curriculum_id=selected_curriculum["id"] if selected_curriculum else None,
                )

                messages.append(
                    {
                        "role": "assistant",
                        "question": question,
                        "result": result,
                        "recommended_answer": None,
                    }
                )
                st.rerun()

            except Exception as exc:
                st.error(f"Could not answer: {exc}")
