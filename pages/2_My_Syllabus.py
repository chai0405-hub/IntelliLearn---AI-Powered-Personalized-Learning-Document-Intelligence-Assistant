import streamlit as st

from utils.auth import require_auth, render_sidebar
from utils.pdf_utils import extract_pages
from utils.curriculum import analyze_curriculum_sources, embed_topic_rows
from utils.gemini_client import embed_texts
from utils.db import (
    create_curriculum,
    create_curriculum_unit,
    delete_curriculum,
    get_relevant_topics,
    insert_curriculum_questions,
    insert_curriculum_topics,
    list_curricula,
    list_curriculum_questions,
    list_curriculum_topics,
    list_curriculum_units,
    upload_pdf_file,
)


st.set_page_config(
    page_title="My Syllabus | IntelliLearn",
    page_icon="📚",
    layout="wide",
)
require_auth()
render_sidebar()

st.title("My Syllabus")
st.caption(
    "Step 1: upload a syllabus, a question bank, or both. IntelliLearn builds a curriculum map before you add textbooks/notes."
)

with st.expander("Create a new curriculum", expanded=not bool(list_curricula())):
    st.markdown("### 1. Course details")
    c1, c2, c3 = st.columns(3)
    subject_hint = c1.text_input("Subject name", placeholder="Example: Machine Learning")
    course_hint = c2.text_input("Course / Program", placeholder="Example: B.Tech CSE")
    semester_hint = c3.text_input("Semester", placeholder="Example: V")

    st.markdown("### 2. Upload curriculum sources")
    left, right = st.columns(2)
    with left:
        syllabus_file = st.file_uploader(
            "Syllabus PDF (optional)",
            type=["pdf"],
            key="syllabus_upload",
            help="Best source for official Unit/Module mapping.",
        )
    with right:
        question_bank_file = st.file_uploader(
            "Question Bank PDF (optional)",
            type=["pdf"],
            key="question_bank_upload",
            help="Used to identify exam-oriented topics and related questions.",
        )

    st.info(
        "At least one PDF is required. If only a question bank is supplied and it has no printed unit labels, "
        "IntelliLearn marks the extracted topic structure as inferred, not official."
    )

    if st.button("Analyze & Create Curriculum", type="primary", use_container_width=True):
        if syllabus_file is None and question_bank_file is None:
            st.error("Upload a syllabus, a question bank, or both.")
        else:
            created_curriculum_id = None
            try:
                status = st.status("Building curriculum intelligence...", expanded=True)

                syllabus_pages = None
                question_pages = None

                if syllabus_file is not None:
                    status.write("1/7 Extracting syllabus text")
                    syllabus_pages = extract_pages(syllabus_file.getvalue(), max_pages=120)
                    if not syllabus_pages:
                        raise ValueError("No selectable text was found in the syllabus PDF.")

                if question_bank_file is not None:
                    status.write("2/7 Extracting question-bank text")
                    question_pages = extract_pages(question_bank_file.getvalue(), max_pages=120)
                    if not question_pages:
                        raise ValueError("No selectable text was found in the question bank PDF.")

                status.write("3/7 Detecting units, modules, topics and question patterns")
                analysis = analyze_curriculum_sources(
                    syllabus_pages=syllabus_pages,
                    question_bank_pages=question_pages,
                    subject_hint=subject_hint,
                    course_hint=course_hint,
                    semester_hint=semester_hint,
                )

                if not analysis.get("units"):
                    raise ValueError("No curriculum units/topics could be extracted from the supplied PDF(s).")

                source_type = (
                    "syllabus+question_bank"
                    if syllabus_file is not None and question_bank_file is not None
                    else "syllabus"
                    if syllabus_file is not None
                    else "question_bank"
                )

                status.write("4/7 Saving source PDFs securely")
                syllabus_path = None
                question_path = None
                if syllabus_file is not None:
                    syllabus_path = upload_pdf_file(
                        st.session_state.user_id,
                        syllabus_file.name,
                        syllabus_file.getvalue(),
                        folder="curriculum",
                    )
                if question_bank_file is not None:
                    question_path = upload_pdf_file(
                        st.session_state.user_id,
                        question_bank_file.name,
                        question_bank_file.getvalue(),
                        folder="curriculum",
                    )

                curriculum = create_curriculum(
                    user_id=st.session_state.user_id,
                    subject_name=(subject_hint.strip() or analysis.get("subject_name") or "Untitled Subject"),
                    course_name=(course_hint.strip() or analysis.get("course_name") or ""),
                    semester=(semester_hint.strip() or analysis.get("semester") or ""),
                    source_type=source_type,
                    syllabus_filename=syllabus_file.name if syllabus_file is not None else None,
                    syllabus_storage_path=syllabus_path,
                    question_bank_filename=question_bank_file.name if question_bank_file is not None else None,
                    question_bank_storage_path=question_path,
                )
                created_curriculum_id = curriculum["id"]

                status.write("5/7 Saving units and semantic topic embeddings")
                raw_topic_rows = []
                unit_lookup = {}
                global_topic_order = 0

                for unit_order, unit in enumerate(analysis["units"], start=1):
                    unit_row = create_curriculum_unit(
                        curriculum_id=curriculum["id"],
                        unit_number=str(unit.get("unit_number") or "").strip(),
                        unit_title=str(unit.get("unit_title") or f"Unit {unit_order}").strip(),
                        is_official=bool(unit.get("is_official")),
                        sort_order=unit_order,
                    )
                    unit_lookup[str(unit.get("unit_number") or "").strip().lower()] = unit_row

                    for topic in unit.get("topics") or []:
                        global_topic_order += 1
                        raw_topic_rows.append(
                            {
                                "curriculum_id": curriculum["id"],
                                "unit_id": unit_row["id"],
                                "topic_name": topic["topic_name"],
                                "topic_description": topic.get("topic_description", ""),
                                "is_official": bool(topic.get("is_official", unit.get("is_official", False))),
                                "sort_order": global_topic_order,
                            }
                        )

                # Defensive fallback for question-bank-only PDFs where the model found
                # question topics but returned no explicit topic list.
                if not raw_topic_rows and analysis.get("questions"):
                    first_unit = list_curriculum_units(curriculum["id"])[0]
                    seen = set()
                    for question in analysis["questions"]:
                        hint = str(question.get("topic_hint") or "").strip()
                        if hint and hint.lower() not in seen:
                            seen.add(hint.lower())
                            global_topic_order += 1
                            raw_topic_rows.append(
                                {
                                    "curriculum_id": curriculum["id"],
                                    "unit_id": first_unit["id"],
                                    "topic_name": hint,
                                    "topic_description": "Inferred from uploaded question bank.",
                                    "is_official": False,
                                    "sort_order": global_topic_order,
                                }
                            )

                topic_rows = embed_topic_rows(raw_topic_rows)
                insert_curriculum_topics(topic_rows)

                status.write("6/7 Mapping question-bank questions to curriculum topics")
                questions = (analysis.get("questions") or [])[:100]
                question_rows = []
                if questions and topic_rows:
                    q_vectors = []
                    batch_size = 20
                    q_texts = [str(q.get("question_text") or "").strip() for q in questions]
                    for start in range(0, len(q_texts), batch_size):
                        q_vectors.extend(
                            embed_texts(
                                q_texts[start : start + batch_size],
                                task_type="RETRIEVAL_QUERY",
                            )
                        )

                    for q, vector in zip(questions, q_vectors):
                        matches = get_relevant_topics(curriculum["id"], vector, match_count=1)
                        best = matches[0] if matches else None
                        question_rows.append(
                            {
                                "curriculum_id": curriculum["id"],
                                "unit_id": best.get("unit_id") if best else None,
                                "topic_id": best.get("id") if best else None,
                                "question_text": str(q.get("question_text") or "").strip(),
                                "topic_hint": str(q.get("topic_hint") or "").strip(),
                            }
                        )
                    insert_curriculum_questions(question_rows)

                status.write("7/7 Curriculum map ready")
                status.update(label="Curriculum created successfully.", state="complete")
                st.session_state.active_curriculum_id = curriculum["id"]
                st.success("Curriculum Intelligence is ready. Next, upload a textbook or notes and attach them to this curriculum.")
                st.rerun()

            except Exception as exc:
                if created_curriculum_id:
                    try:
                        delete_curriculum(created_curriculum_id)
                    except Exception:
                        pass
                st.error(f"Could not create curriculum: {exc}")


st.divider()
st.subheader("Your curricula")

curricula = list_curricula()
if not curricula:
    st.info("No curriculum has been created yet.")
    st.stop()

for curriculum in curricula:
    units = list_curriculum_units(curriculum["id"])
    topics = list_curriculum_topics(curriculum["id"])
    questions = list_curriculum_questions(curriculum["id"], limit=200)

    with st.container(border=True):
        top1, top2, top3, top4 = st.columns([2.2, 1.2, 1, 1])
        top1.markdown(f"### {curriculum['subject_name']}")
        details = " · ".join(
            x for x in [curriculum.get("course_name"), curriculum.get("semester")] if x
        )
        if details:
            top1.caption(details)
        top2.metric("Units", len(units))
        top3.metric("Topics", len(topics))
        top4.metric("QB Questions", len(questions))

        source_text = curriculum.get("source_type", "").replace("_", " + ").title()
        st.caption(f"Curriculum source: {source_text}")

        if st.button("Use this curriculum", key=f"use_curr_{curriculum['id']}"):
            st.session_state.active_curriculum_id = curriculum["id"]
            st.success(f"Active curriculum set to {curriculum['subject_name']}.")

        with st.expander("View unit / topic map"):
            topics_by_unit = {}
            for topic in topics:
                topics_by_unit.setdefault(topic["unit_id"], []).append(topic)

            for unit in units:
                official = "Official syllabus" if unit.get("is_official") else "Inferred / question-bank structure"
                label = f"{unit.get('unit_number') or ''} {unit.get('unit_title') or ''}".strip()
                st.markdown(f"**{label}** — {official}")
                unit_topics = topics_by_unit.get(unit["id"], [])
                if unit_topics:
                    st.write(" • " + "\n • ".join(t["topic_name"] for t in unit_topics))
                else:
                    st.caption("No topics extracted for this unit.")
