import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.db import (
    create_document,
    insert_document_chunks,
    list_curricula,
    list_documents,
    upload_document_file,
)
from utils.pdf_utils import extract_pages, build_page_chunks
from utils.gemini_client import embed_texts


st.set_page_config(
    page_title="My Documents | IntelliLearn",
    page_icon="📄",
    layout="wide",
)
require_auth()
render_sidebar()

st.title("My Documents")
st.caption(
    "Step 2: upload textbooks, notes or reference PDFs. Attach them to a curriculum when available."
)

curricula = list_curricula()
curriculum_by_label = {
    f"{c['subject_name']}" + (f" · {c['semester']}" if c.get("semester") else ""): c
    for c in curricula
}

with st.container(border=True):
    st.markdown("### Add study material")

    c1, c2 = st.columns(2)
    document_type = c1.selectbox(
        "Document type",
        ["Textbook", "Notes", "Reference Material"],
    )

    curriculum_options = ["No curriculum / document only"] + list(curriculum_by_label.keys())
    default_curriculum_index = 0
    active_curriculum_id = st.session_state.get("active_curriculum_id")
    if active_curriculum_id:
        for i, label in enumerate(curriculum_options[1:], start=1):
            if curriculum_by_label[label]["id"] == active_curriculum_id:
                default_curriculum_index = i
                break

    selected_curriculum_label = c2.selectbox(
        "Attach to curriculum",
        curriculum_options,
        index=default_curriculum_index,
        help="This allows syllabus-aware retrieval and unit/topic matching.",
    )

    uploaded = st.file_uploader(
        "Upload textbook / notes PDF",
        type=["pdf"],
        accept_multiple_files=False,
    )

    selected_curriculum = (
        curriculum_by_label.get(selected_curriculum_label)
        if selected_curriculum_label != "No curriculum / document only"
        else None
    )

    if uploaded is not None:
        size_mb = uploaded.size / (1024 * 1024)
        st.caption(f"{uploaded.name} — {size_mb:.2f} MB")

        if size_mb > 25:
            st.error("Please upload a PDF smaller than 25 MB.")
        elif st.button("Process document", type="primary", use_container_width=True):
            pdf_bytes = uploaded.getvalue()

            try:
                status = st.status("Processing study material...", expanded=True)

                status.write("1/5 Extracting PDF text")
                pages = extract_pages(pdf_bytes, max_pages=120)
                if not pages:
                    raise ValueError(
                        "No selectable text was found. Scanned-image PDFs need OCR, which is not enabled in this version."
                    )

                status.write("2/5 Splitting text into page-aware chunks")
                chunks = build_page_chunks(pages, max_chunks=350)
                if not chunks:
                    raise ValueError("No text chunks were produced.")

                status.write("3/5 Uploading the original PDF to secure storage")
                storage_path = upload_document_file(
                    st.session_state.user_id,
                    uploaded.name,
                    pdf_bytes,
                )

                status.write("4/5 Creating the document record")
                document = create_document(
                    user_id=st.session_state.user_id,
                    filename=uploaded.name,
                    storage_path=storage_path,
                    page_count=max(p["page_number"] for p in pages),
                    document_type=document_type.lower().replace(" ", "_"),
                    curriculum_id=selected_curriculum["id"] if selected_curriculum else None,
                )

                status.write(f"5/5 Creating embeddings for {len(chunks)} chunks")
                progress = st.progress(0)
                rows = []
                batch_size = 20

                for start in range(0, len(chunks), batch_size):
                    batch = chunks[start : start + batch_size]
                    vectors = embed_texts(
                        [x["content"] for x in batch],
                        task_type="RETRIEVAL_DOCUMENT",
                    )

                    for chunk, vector in zip(batch, vectors):
                        rows.append(
                            {
                                "user_id": st.session_state.user_id,
                                "document_id": document["id"],
                                "page_number": chunk["page_number"],
                                "chunk_index": chunk["chunk_index"],
                                "content": chunk["content"],
                                "embedding": vector,
                            }
                        )

                    progress.progress(min((start + len(batch)) / len(chunks), 1.0))

                insert_document_chunks(rows)
                status.update(label="Study material is ready.", state="complete")
                st.success("Document processed successfully.")
                if selected_curriculum:
                    st.info(
                        f"Mapped to curriculum: {selected_curriculum['subject_name']}. "
                        "Ask IntelliLearn can now use syllabus-aware fallback logic."
                    )
                st.rerun()

            except Exception as exc:
                st.error(f"Processing failed: {exc}")


st.divider()
st.subheader("Your indexed study materials")

documents = list_documents()
if not documents:
    st.info("No study materials uploaded yet.")
else:
    curriculum_name_by_id = {c["id"]: c["subject_name"] for c in curricula}

    for doc in documents:
        with st.container(border=True):
            cols = st.columns([3, 1.1, 1.4, 1])
            cols[0].markdown(f"**{doc['filename']}**")
            cols[0].caption(doc.get("document_type", "document").replace("_", " ").title())
            cols[1].write(f"{doc['page_count']} pages")
            mapped_name = curriculum_name_by_id.get(doc.get("curriculum_id"))
            cols[2].write(mapped_name or "Document only")

            if cols[3].button("Ask AI", key=f"ask_{doc['id']}"):
                st.session_state.selected_document_id = doc["id"]
                if doc.get("curriculum_id"):
                    st.session_state.active_curriculum_id = doc["curriculum_id"]
                st.switch_page("pages/3_Ask_IntelliLearn.py")
