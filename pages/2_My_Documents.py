import streamlit as st
from utils.auth import require_auth, render_sidebar
from utils.db import (
    list_documents,
    upload_document_file,
    create_document,
    insert_document_chunks,
)
from utils.pdf_utils import extract_pages, build_page_chunks
from utils.gemini_client import embed_texts

st.set_page_config(page_title="My Documents | IntelliLearn", page_icon="📄", layout="wide")
require_auth()
render_sidebar()

st.title("My Documents")
st.write("Upload a PDF. IntelliLearn will extract, chunk, embed and index the document for RAG.")

uploaded = st.file_uploader(
    "Upload study material",
    type=["pdf"],
    accept_multiple_files=False,
)

if uploaded is not None:
    size_mb = uploaded.size / (1024 * 1024)
    st.caption(f"{uploaded.name} — {size_mb:.2f} MB")

    if size_mb > 25:
        st.error("Please upload a PDF smaller than 25 MB.")
    elif st.button("Process document", type="primary"):
        pdf_bytes = uploaded.getvalue()

        try:
            status = st.status("Processing document...", expanded=True)

            status.write("1/5 Extracting PDF text")
            pages = extract_pages(pdf_bytes, max_pages=100)
            if not pages:
                raise ValueError(
                    "No selectable text was found. This starter does not OCR scanned PDFs yet."
                )

            status.write("2/5 Splitting text into chunks")
            chunks = build_page_chunks(pages, max_chunks=300)
            if not chunks:
                raise ValueError("No text chunks were produced.")

            status.write("3/5 Uploading original PDF to secure storage")
            storage_path = upload_document_file(
                st.session_state.user_id,
                uploaded.name,
                pdf_bytes,
            )

            status.write("4/5 Creating document record")
            document = create_document(
                st.session_state.user_id,
                uploaded.name,
                storage_path,
                page_count=max(p["page_number"] for p in pages),
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
            status.update(label="Document ready for AI questions.", state="complete")
            st.success("Document processed successfully.")
            st.rerun()

        except Exception as exc:
            st.error(f"Processing failed: {exc}")

st.divider()
st.subheader("Your indexed documents")

documents = list_documents()

if not documents:
    st.info("No documents uploaded yet.")
else:
    for doc in documents:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            cols[0].markdown(f"**{doc['filename']}**")
            cols[1].write(f"{doc['page_count']} pages")
            if cols[2].button("Ask AI", key=f"ask_{doc['id']}"):
                st.session_state.selected_document_id = doc["id"]
                st.switch_page("pages/3_Ask_IntelliLearn.py")
