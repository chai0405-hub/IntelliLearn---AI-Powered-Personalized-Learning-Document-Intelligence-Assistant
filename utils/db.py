from datetime import date
from uuid import uuid4
from utils.supabase_client import get_supabase


def _safe_filename(filename: str) -> str:
    return filename.replace("/", "_").replace("\\", "_")


def upload_pdf_file(
    user_id: str,
    filename: str,
    pdf_bytes: bytes,
    folder: str = "study",
) -> str:
    supabase = get_supabase()
    safe_name = _safe_filename(filename)
    storage_path = f"{user_id}/{folder}/{uuid4()}-{safe_name}"

    supabase.storage.from_("documents").upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={
            "content-type": "application/pdf",
            "upsert": "false",
        },
    )
    return storage_path


# Backward-compatible alias used by older code.
def upload_document_file(user_id: str, filename: str, pdf_bytes: bytes) -> str:
    return upload_pdf_file(user_id, filename, pdf_bytes, folder="study")


# ============================================================
# CURRICULUM / SYLLABUS
# ============================================================


def create_curriculum(
    user_id: str,
    subject_name: str,
    course_name: str,
    semester: str,
    source_type: str,
    syllabus_filename: str | None = None,
    syllabus_storage_path: str | None = None,
    question_bank_filename: str | None = None,
    question_bank_storage_path: str | None = None,
):
    supabase = get_supabase()
    response = (
        supabase.table("curricula")
        .insert(
            {
                "user_id": user_id,
                "subject_name": subject_name.strip() or "Untitled Subject",
                "course_name": course_name.strip(),
                "semester": semester.strip(),
                "source_type": source_type,
                "syllabus_filename": syllabus_filename,
                "syllabus_storage_path": syllabus_storage_path,
                "question_bank_filename": question_bank_filename,
                "question_bank_storage_path": question_bank_storage_path,
            }
        )
        .execute()
    )
    return response.data[0]


def list_curricula():
    response = (
        get_supabase()
        .table("curricula")
        .select(
            "id, subject_name, course_name, semester, source_type, "
            "syllabus_filename, question_bank_filename, created_at"
        )
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_curriculum(curriculum_id: str):
    response = (
        get_supabase()
        .table("curricula")
        .select("*")
        .eq("id", curriculum_id)
        .maybe_single()
        .execute()
    )
    return response.data


def create_curriculum_unit(
    curriculum_id: str,
    unit_number: str,
    unit_title: str,
    is_official: bool,
    sort_order: int,
):
    response = (
        get_supabase()
        .table("curriculum_units")
        .insert(
            {
                "curriculum_id": curriculum_id,
                "unit_number": unit_number,
                "unit_title": unit_title,
                "is_official": is_official,
                "sort_order": sort_order,
            }
        )
        .execute()
    )
    return response.data[0]


def list_curriculum_units(curriculum_id: str):
    response = (
        get_supabase()
        .table("curriculum_units")
        .select("id, curriculum_id, unit_number, unit_title, is_official, sort_order")
        .eq("curriculum_id", curriculum_id)
        .order("sort_order")
        .execute()
    )
    return response.data or []


def insert_curriculum_topics(rows: list[dict]):
    if not rows:
        return
    supabase = get_supabase()
    for start in range(0, len(rows), 50):
        supabase.table("curriculum_topics").insert(rows[start : start + 50]).execute()


def list_curriculum_topics(curriculum_id: str, unit_id: str | None = None):
    query = (
        get_supabase()
        .table("curriculum_topics")
        .select(
            "id, curriculum_id, unit_id, topic_name, topic_description, "
            "is_official, sort_order"
        )
        .eq("curriculum_id", curriculum_id)
    )
    if unit_id:
        query = query.eq("unit_id", unit_id)
    response = query.order("sort_order").execute()
    return response.data or []


def get_relevant_topics(
    curriculum_id: str,
    query_embedding: list[float],
    match_count: int = 5,
):
    response = get_supabase().rpc(
        "match_curriculum_topics",
        {
            "query_embedding": query_embedding,
            "p_curriculum_id": curriculum_id,
            "match_count": match_count,
        },
    ).execute()
    return response.data or []


def insert_curriculum_questions(rows: list[dict]):
    if not rows:
        return
    supabase = get_supabase()
    for start in range(0, len(rows), 50):
        supabase.table("curriculum_questions").insert(rows[start : start + 50]).execute()


def list_curriculum_questions(
    curriculum_id: str,
    unit_id: str | None = None,
    limit: int = 100,
):
    query = (
        get_supabase()
        .table("curriculum_questions")
        .select("id, curriculum_id, unit_id, topic_id, question_text, topic_hint, created_at")
        .eq("curriculum_id", curriculum_id)
    )
    if unit_id:
        query = query.eq("unit_id", unit_id)
    response = query.limit(limit).execute()
    return response.data or []


def delete_curriculum(curriculum_id: str):
    get_supabase().table("curricula").delete().eq("id", curriculum_id).execute()


# ============================================================
# DOCUMENTS
# ============================================================


def list_documents(curriculum_id: str | None = None):
    query = (
        get_supabase()
        .table("documents")
        .select(
            "id, filename, page_count, document_type, curriculum_id, created_at"
        )
    )
    if curriculum_id:
        query = query.eq("curriculum_id", curriculum_id)
    response = query.order("created_at", desc=True).execute()
    return response.data or []


def create_document(
    user_id: str,
    filename: str,
    storage_path: str,
    page_count: int,
    document_type: str = "notes",
    curriculum_id: str | None = None,
):
    response = (
        get_supabase()
        .table("documents")
        .insert(
            {
                "user_id": user_id,
                "filename": filename,
                "storage_path": storage_path,
                "page_count": page_count,
                "document_type": document_type,
                "curriculum_id": curriculum_id,
            }
        )
        .execute()
    )
    return response.data[0]


def insert_document_chunks(rows: list[dict]):
    if not rows:
        return
    supabase = get_supabase()
    for start in range(0, len(rows), 50):
        supabase.table("document_chunks").insert(rows[start : start + 50]).execute()


def delete_document(document_id: str, storage_path: str | None = None):
    supabase = get_supabase()
    if storage_path:
        try:
            supabase.storage.from_("documents").remove([storage_path])
        except Exception:
            pass
    supabase.table("documents").delete().eq("id", document_id).execute()


def get_document(document_id: str):
    response = (
        get_supabase()
        .table("documents")
        .select(
            "id, filename, storage_path, page_count, document_type, "
            "curriculum_id, created_at"
        )
        .eq("id", document_id)
        .maybe_single()
        .execute()
    )
    return response.data


def get_relevant_chunks(
    document_id: str,
    query_embedding: list[float],
    match_count: int = 6,
):
    response = get_supabase().rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "p_document_id": document_id,
            "match_count": match_count,
        },
    ).execute()
    return response.data or []


def get_relevant_curriculum_chunks(
    curriculum_id: str,
    query_embedding: list[float],
    match_count: int = 8,
):
    response = get_supabase().rpc(
        "match_curriculum_document_chunks",
        {
            "query_embedding": query_embedding,
            "p_curriculum_id": curriculum_id,
            "match_count": match_count,
        },
    ).execute()
    return response.data or []


# ============================================================
# QUIZ / STUDY PLAN
# ============================================================


def save_quiz_attempt(topic: str, score: int, total: int):
    percentage = round((score / total) * 100, 2) if total else 0
    get_supabase().table("quiz_attempts").insert(
        {
            "topic": topic,
            "score": score,
            "total": total,
            "percentage": percentage,
        }
    ).execute()


def get_quiz_attempts():
    response = (
        get_supabase()
        .table("quiz_attempts")
        .select("topic, score, total, percentage, created_at")
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


def save_study_plan(
    exam_date: date,
    daily_minutes: int,
    subjects: list[str],
    plan_markdown: str,
):
    get_supabase().table("study_plans").insert(
        {
            "exam_date": exam_date.isoformat(),
            "daily_minutes": daily_minutes,
            "subjects": subjects,
            "plan_markdown": plan_markdown,
        }
    ).execute()
