from utils.gemini_client import embed_texts, generate_text
from utils.db import get_relevant_chunks


def retrieve(document_id: str, query: str, match_count: int = 6):
    query_vector = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    return get_relevant_chunks(
        document_id=document_id,
        query_embedding=query_vector,
        match_count=match_count,
    )


def answer_from_document(document_id: str, question: str):
    chunks = retrieve(document_id, question, match_count=6)
    if not chunks:
        return (
            "I could not find enough relevant information in this document.",
            [],
        )

    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"[SOURCE {idx} | Page {chunk['page_number']}]\n{chunk['content']}"
        )

    context = "\n\n".join(context_blocks)

    prompt = f"""
You are IntelliLearn, a document-grounded educational assistant.

RULES:
1. Answer using ONLY the supplied document context.
2. If the context does not contain enough information, clearly say so.
3. Explain the answer in student-friendly language.
4. Cite supporting pages inline like [Page 12].
5. Do not invent page numbers or facts.
6. Prefer a concise explanation, then examples/bullets if helpful.

DOCUMENT CONTEXT:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""
    answer = generate_text(prompt)
    return answer, chunks
