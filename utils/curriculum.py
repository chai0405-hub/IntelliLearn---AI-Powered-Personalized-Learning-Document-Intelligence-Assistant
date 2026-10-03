from __future__ import annotations

from utils.gemini_client import embed_texts, generate_json, generate_text
from utils.db import get_relevant_topics


SYLLABUS_MATCH_THRESHOLD = 0.58


def _pages_to_text(pages: list[dict], max_chars: int = 45000) -> str:
    blocks = []
    total = 0
    for page in pages:
        block = f"\n[Page {page['page_number']}]\n{page['text']}\n"
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 0:
                blocks.append(block[:remaining])
            break
        blocks.append(block)
        total += len(block)
    return "".join(blocks)


def analyze_curriculum_sources(
    syllabus_pages: list[dict] | None,
    question_bank_pages: list[dict] | None,
    subject_hint: str = "",
    course_hint: str = "",
    semester_hint: str = "",
) -> dict:
    """
    Convert syllabus/question-bank PDFs into a structured curriculum map.
    Official unit labels are only accepted when they are explicit in the source.
    Question-bank-only topics are marked inferred/non-official.
    """
    syllabus_text = _pages_to_text(syllabus_pages or [])
    question_text = _pages_to_text(question_bank_pages or [])

    if not syllabus_text and not question_text:
        raise ValueError("Provide a syllabus, question bank, or both.")

    prompt = f"""
You are the curriculum parser inside IntelliLearn.

Your task is to create a faithful curriculum map from the supplied source text.
Do NOT invent official unit/module numbers or titles.

USER HINTS (may be blank):
Subject: {subject_hint}
Course: {course_hint}
Semester: {semester_hint}

SYLLABUS SOURCE:
{syllabus_text if syllabus_text else '[No syllabus PDF supplied]'}

QUESTION BANK SOURCE:
{question_text if question_text else '[No question bank PDF supplied]'}

Return JSON only with this exact top-level structure:
{{
  "subject_name": "",
  "course_name": "",
  "semester": "",
  "units": [
    {{
      "unit_number": "I",
      "unit_title": "Classification",
      "is_official": true,
      "topics": [
        {{
          "topic_name": "Naive Bayes Classifier",
          "topic_description": "Short description based only on the source wording",
          "is_official": true
        }}
      ]
    }}
  ],
  "questions": [
    {{
      "question_text": "Exact or lightly cleaned question text from the question bank",
      "topic_hint": "Naive Bayes Classifier",
      "unit_number_hint": "III"
    }}
  ]
}}

RULES:
1. Prefer the user's Subject/Course/Semester hints when they are provided.
2. If a syllabus is supplied, preserve its actual Unit/Module numbering and titles.
3. Every syllabus topic must be placed under the unit/module where it appears.
4. Never invent an official unit number.
5. If ONLY a question bank is supplied and it has no explicit unit/module structure,
   create ONE unit with unit_number="QB", unit_title="Question Bank Topics",
   is_official=false. Put inferred exam topics under it with is_official=false.
6. If the question bank itself explicitly prints unit/module labels, preserve those labels.
7. Questions must come from the question bank only. Do not invent questions.
8. Keep topic names concise and de-duplicate obvious repetitions.
9. If a field is not available, use an empty string rather than guessing.
"""

    data = generate_json(prompt)
    if not isinstance(data, dict):
        raise ValueError("The AI returned an unexpected curriculum format.")

    data.setdefault("subject_name", subject_hint or "Untitled Subject")
    data.setdefault("course_name", course_hint or "")
    data.setdefault("semester", semester_hint or "")
    data.setdefault("units", [])
    data.setdefault("questions", [])

    # Defensive normalization.
    normalized_units = []
    seen_units = set()
    for u_index, unit in enumerate(data.get("units") or [], start=1):
        if not isinstance(unit, dict):
            continue
        number = str(unit.get("unit_number") or "").strip()
        title = str(unit.get("unit_title") or "").strip() or f"Unit {u_index}"
        key = (number.lower(), title.lower())
        if key in seen_units:
            continue
        seen_units.add(key)

        topics = []
        seen_topics = set()
        for topic in unit.get("topics") or []:
            if isinstance(topic, str):
                topic = {"topic_name": topic}
            if not isinstance(topic, dict):
                continue
            name = str(topic.get("topic_name") or "").strip()
            if not name or name.lower() in seen_topics:
                continue
            seen_topics.add(name.lower())
            topics.append(
                {
                    "topic_name": name,
                    "topic_description": str(topic.get("topic_description") or "").strip(),
                    "is_official": bool(topic.get("is_official", unit.get("is_official", False))),
                }
            )

        normalized_units.append(
            {
                "unit_number": number,
                "unit_title": title,
                "is_official": bool(unit.get("is_official", False)),
                "topics": topics,
            }
        )

    # If question-bank-only parsing came back with no units, create a safe inferred bucket.
    if not normalized_units and question_text:
        normalized_units = [
            {
                "unit_number": "QB",
                "unit_title": "Question Bank Topics",
                "is_official": False,
                "topics": [],
            }
        ]

    data["units"] = normalized_units
    data["questions"] = [
        q
        for q in (data.get("questions") or [])
        if isinstance(q, dict) and str(q.get("question_text") or "").strip()
    ]
    return data


def embed_topic_rows(topic_rows: list[dict]) -> list[dict]:
    if not topic_rows:
        return []

    output = []
    batch_size = 20
    for start in range(0, len(topic_rows), batch_size):
        batch = topic_rows[start : start + batch_size]
        texts = [
            f"{row['topic_name']}. {row.get('topic_description', '')}".strip()
            for row in batch
        ]
        vectors = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
        for row, vector in zip(batch, vectors):
            item = dict(row)
            item["embedding"] = vector
            output.append(item)
    return output


def match_question_to_curriculum(
    curriculum_id: str,
    question: str,
    threshold: float = SYLLABUS_MATCH_THRESHOLD,
) -> dict | None:
    query_vector = embed_texts([question], task_type="RETRIEVAL_QUERY")[0]
    matches = get_relevant_topics(curriculum_id, query_vector, match_count=5)
    if not matches:
        return None

    top = dict(matches[0])
    top["similarity"] = float(top.get("similarity") or 0)
    top["in_scope"] = top["similarity"] >= threshold
    top["candidates"] = matches
    return top


def assess_context_sufficiency(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "sufficient": False,
            "reason": "No relevant document passages were retrieved.",
        }

    context = "\n\n".join(
        f"[Page {x.get('page_number')} | similarity {float(x.get('similarity', 0)):.3f}]\n{x.get('content', '')}"
        for x in chunks[:8]
    )

    prompt = f"""
Decide whether the supplied study-material context contains enough factual information
to answer the student's question without relying on outside knowledge.

QUESTION:
{question}

CONTEXT:
{context}

Return JSON only:
{{
  "sufficient": true,
  "reason": "one short reason"
}}

Be strict. A passage merely mentioning the same topic is NOT sufficient if it does not
contain the information needed by the question.
"""

    try:
        result = generate_json(prompt)
        return {
            "sufficient": bool(result.get("sufficient")),
            "reason": str(result.get("reason") or ""),
        }
    except Exception:
        max_similarity = max(float(x.get("similarity", 0)) for x in chunks)
        return {
            "sufficient": max_similarity >= 0.72,
            "reason": "Fallback similarity check was used.",
        }


def generate_syllabus_guided_answer(question: str, curriculum_match: dict) -> str:
    official_label = (
        "official syllabus topic"
        if curriculum_match.get("is_official")
        else "question-bank/inferred curriculum topic"
    )

    prompt = f"""
You are IntelliLearn's syllabus-guided educational assistant.

The uploaded study material did NOT contain enough information to answer the question.
The question has been mapped to this curriculum topic:

Subject: {curriculum_match.get('subject_name', '')}
Unit/Module: {curriculum_match.get('unit_number', '')} - {curriculum_match.get('unit_title', '')}
Topic: {curriculum_match.get('topic_name', '')}
Mapping type: {official_label}

STUDENT QUESTION:
{question}

Generate a clear, exam-appropriate recommended answer using your general educational
knowledge, but keep it tightly within the mapped curriculum topic.

Requirements:
- Start directly with the answer.
- Use simple student-friendly language.
- Use bullets/steps/examples where useful.
- Do not claim the answer came from the uploaded textbook/notes.
- Do not invent a textbook page number or citation.
- If the question itself is ambiguous, say what interpretation you are using.
"""
    return generate_text(prompt)
