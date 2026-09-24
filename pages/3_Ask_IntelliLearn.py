import streamlit as st
from utils.auth import require_auth, render_sidebar
from utils.db import list_documents
from utils.rag import answer_from_document

st.set_page_config(page_title="Ask IntelliLearn", page_icon="💬", layout="wide")
require_auth()
render_sidebar()

st.title("Ask IntelliLearn")
st.caption("Answers are grounded in your selected PDF and include source pages.")

documents = list_documents()
if not documents:
    st.info("Upload and process a PDF first.")
    if st.button("Go to My Documents"):
        st.switch_page("pages/2_My_Documents.py")
    st.stop()

doc_by_name = {doc["filename"]: doc for doc in documents}
default_index = 0
selected_id = st.session_state.get("selected_document_id")
for idx, doc in enumerate(documents):
    if doc["id"] == selected_id:
        default_index = idx
        break

selected_name = st.selectbox(
    "Document",
    options=[doc["filename"] for doc in documents],
    index=default_index,
)
selected_doc = doc_by_name[selected_name]
st.session_state.selected_document_id = selected_doc["id"]

chat_key = f"chat_{selected_doc['id']}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

for message in st.session_state[chat_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(
                        f"Page {source['page_number']} "
                        f"(similarity {float(source.get('similarity', 0)):.2f})"
                    )

question = st.chat_input("Ask a question from this document...")

if question:
    st.session_state[chat_key].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching your document and generating an answer..."):
            try:
                answer, sources = answer_from_document(selected_doc["id"], question)
                st.markdown(answer)

                compact_sources = [
                    {
                        "page_number": x["page_number"],
                        "similarity": x.get("similarity", 0),
                    }
                    for x in sources
                ]

                with st.expander("Sources"):
                    for source in compact_sources:
                        st.write(
                            f"Page {source['page_number']} "
                            f"(similarity {float(source.get('similarity', 0)):.2f})"
                        )

                st.session_state[chat_key].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": compact_sources,
                    }
                )
            except Exception as exc:
                st.error(f"Could not answer: {exc}")
