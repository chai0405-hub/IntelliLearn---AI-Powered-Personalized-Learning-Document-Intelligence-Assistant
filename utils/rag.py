from __future__ import annotations

from utils.gemini_client import embed_texts, generate_text
from utils.db import (
    get_relevant_chunks,
    get_relevant_curriculum_chunks,
)
from utils.curriculum import (
    assess_context_sufficiency,
    match_question_to_curriculum,
)


def retrieve(document_id: str, query: str, match_count: int = 6):
    query_vector = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    return get_relevant_chunks(
        document_id=document_id,
        query_embedding=query_vector,
        match_count=match_count,
    )


def retrieve_curriculum_materials(
    curriculum_id: str,
    query: str,
    match_count: int = 8,
):
    query_vector = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    return get_relevant_curriculum_chunks(
        curriculum_id=curriculum_id,
        query_embedding=query_vector,
        match_count=match_count,
    )


def _answer_from_chunks(question: str, chunks: list[dict]) -> str:
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        filename = chunk.get("filename") or "Uploaded document"
        page = chunk.get("page_number")
        context_blocks.append(
            f"[SOURCE {idx} | {filename} | Page {page}]\n{chunk.get('content', '')}"
        )

    context = "\n\n".join(context_blocks)

    prompt = f"""
You are IntelliLearn, a source-grounded educational assistant.

RULES:
1. Answer using ONLY the supplied uploaded-material context.
2. If the context is not enough, say that the material is insufficient.
3. Explain in student-friendly language.
4. Cite supporting pages inline like [Page 12].
5. When multiple documents are used, include the filename when useful.
6. Never invent page numbers, textbook claims, or outside facts.
7. Prefer a concise explanation followed by bullets/examples where helpful.

UPLOADED-MATERIAL CONTEXT:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""
    return generate_text(prompt)


def answer_from_document(document_id: str, question: str):
    chunks = retrieve(document_id, question, match_count=8)
    if not chunks:
        return (
            "I could not find enough relevant information in this document.",
            [],
        )

    sufficiency = assess_context_sufficiency(question, chunks)
    if not sufficiency["sufficient"]:
        return (
            "I could not find enough information in this document to answer that question reliably.",
            chunks,
        )

    answer = _answer_from_chunks(question, chunks)
    return answer, chunks


def answer_intelligently(
    question: str,
    mode: str,
    document_id: str | None = None,
    curriculum_id: str | None = None,
) -> dict:
    """
    Modes:
      - document: selected PDF only
      - all_materials: all study documents attached to curriculum
      - syllabus_aware: curriculum classification + all attached materials

    Returns a structured result so UI can distinguish a source-grounded answer
    from a syllabus-guided fallback opportunity.
    """
    curriculum_match = None
    if curriculum_id:
        curriculum_match = match_question_to_curriculum(curriculum_id, question)

    if mode == "document":
        if not document_id:
            raise ValueError("Select a document first.")
        chunks = retrieve(document_id, question, match_count=8)
    else:
        if not curriculum_id:
            raise ValueError("Select a curriculum first.")
        chunks = retrieve_curriculum_materials(curriculum_id, question, match_count=10)

    sufficiency = assess_context_sufficiency(question, chunks)

    # In strict Syllabus-Aware mode, do not answer questions that fail the
    # curriculum scope check even if a study PDF happens to contain related text.
    if mode == "syllabus_aware" and (
        not curriculum_match or not curriculum_match.get("in_scope")
    ):
        return {
            "status": "not_found",
            "answer": None,
            "sources": chunks,
            "curriculum_match": curriculum_match,
            "reason": "Question is outside the configured curriculum scope.",
        }

    if chunks and sufficiency["sufficient"]:
        return {
            "status": "grounded_answer",
            "answer": _answer_from_chunks(question, chunks),
            "sources": chunks,
            "curriculum_match": curriculum_match,
            "reason": sufficiency.get("reason", ""),
        }

    if curriculum_match and curriculum_match.get("in_scope"):
        return {
            "status": "syllabus_fallback",
            "answer": None,
            "sources": chunks,
            "curriculum_match": curriculum_match,
            "reason": sufficiency.get("reason", ""),
        }

    return {
        "status": "not_found",
        "answer": None,
        "sources": chunks,
        "curriculum_match": curriculum_match,
        "reason": sufficiency.get("reason", ""),
    }
