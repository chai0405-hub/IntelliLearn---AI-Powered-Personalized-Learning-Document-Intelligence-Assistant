from datetime import date
from uuid import uuid4
from utils.supabase_client import get_supabase


def list_documents():
    supabase = get_supabase()
    response = (
        supabase.table("documents")
        .select("id, filename, page_count, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def upload_document_file(user_id: str, filename: str, pdf_bytes: bytes) -> str:
    supabase = get_supabase()
    safe_name = filename.replace("/", "_").replace("\\", "_")
    storage_path = f"{user_id}/{uuid4()}-{safe_name}"

    supabase.storage.from_("documents").upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={
            "content-type": "application/pdf",
            "upsert": "false",
        },
    )
    return storage_path


def create_document(user_id: str, filename: str, storage_path: str, page_count: int):
    supabase = get_supabase()
    response = (
        supabase.table("documents")
        .insert(
            {
                "user_id": user_id,
                "filename": filename,
                "storage_path": storage_path,
                "page_count": page_count,
            }
        )
        .execute()
    )
    return response.data[0]


def insert_document_chunks(rows: list[dict]):
    supabase = get_supabase()
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        supabase.table("document_chunks").insert(rows[i : i + batch_size]).execute()


def delete_document(document_id: str, storage_path: str | None = None):
    supabase = get_supabase()
    if storage_path:
        try:
            supabase.storage.from_("documents").remove([storage_path])
        except Exception:
            pass
    supabase.table("documents").delete().eq("id", document_id).execute()


def get_document(document_id: str):
    supabase = get_supabase()
    response = (
        supabase.table("documents")
        .select("id, filename, storage_path, page_count, created_at")
        .eq("id", document_id)
        .maybe_single()
        .execute()
    )
    return response.data


def get_relevant_chunks(document_id: str, query_embedding: list[float], match_count: int = 6):
    supabase = get_supabase()
    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "p_document_id": document_id,
            "match_count": match_count,
        },
    ).execute()
    return response.data or []


def save_quiz_attempt(topic: str, score: int, total: int):
    supabase = get_supabase()
    percentage = round((score / total) * 100, 2) if total else 0
    supabase.table("quiz_attempts").insert(
        {
            "topic": topic,
            "score": score,
            "total": total,
            "percentage": percentage,
        }
    ).execute()


def get_quiz_attempts():
    supabase = get_supabase()
    response = (
        supabase.table("quiz_attempts")
        .select("topic, score, total, percentage, created_at")
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


def save_study_plan(exam_date: date, daily_minutes: int, subjects: list[str], plan_markdown: str):
    supabase = get_supabase()
    supabase.table("study_plans").insert(
        {
            "exam_date": exam_date.isoformat(),
            "daily_minutes": daily_minutes,
            "subjects": subjects,
            "plan_markdown": plan_markdown,
        }
    ).execute()
