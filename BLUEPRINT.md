# IntelliLearn Curriculum Intelligence — Working Cycle / Blueprint

## Core learning cycle

```text
STUDENT
  |
  v
1. CREATE CURRICULUM
   Upload Syllabus PDF and/or Question Bank PDF
  |
  v
2. CURRICULUM ANALYZER
   Extract Subject -> Unit/Module -> Topics -> Question-bank items
  |
  v
3. CURRICULUM KNOWLEDGE MAP
   Store unit/topic embeddings in Supabase pgvector
  |
  v
4. ADD STUDY MATERIAL
   Upload Textbook / Notes / Reference PDF
   Attach it to the curriculum
  |
  v
5. DOCUMENT INTELLIGENCE
   PDF text extraction -> page-aware chunks -> embeddings -> Supabase
  |
  v
6. STUDENT ASKS A QUESTION
  |
  +--> Search selected PDF / all attached materials
  |       |
  |       +--> Sufficient answer found?
  |               |
  |               +--> YES -> PDF-grounded answer + filename + page
  |               |
  |               +--> NO
  |                    |
  |                    v
  |              Match question to syllabus topics
  |                    |
  |                    +--> In syllabus?
  |                           |
  |                           +--> YES -> Offer "Generate Recommended Answer"
  |                           |          -> clearly label as Syllabus-Guided AI
  |                           |          -> no fake textbook citation
  |                           |
  |                           +--> NO -> Say not found / outside curriculum scope
  |
  v
7. QUIZ / FLASHCARDS
   Document-only OR Syllabus Unit
   Facts remain grounded in uploaded study material
  |
  v
8. STUDY PLAN + PROGRESS
   Use syllabus topics + question-bank emphasis + quiz weakness
```

## Source hierarchy

1. **Selected PDF** — highest priority for Document Only mode.
2. **All study materials attached to the curriculum** — used in All My Materials and Syllabus-Aware modes.
3. **Syllabus / question-bank map** — determines whether the question belongs to the student's curriculum.
4. **General Gemini knowledge** — used only after the student explicitly clicks **Generate Recommended Answer** when the topic is in curriculum but the uploaded study material is insufficient.

## Trust labels

- **PDF Source** — answer comes from uploaded study material and shows page/source.
- **Syllabus-Guided AI** — material was insufficient; AI answer is curriculum-scoped and clearly labelled as not coming from the textbook.
- **Outside / Not Found** — no reliable material answer and no strong curriculum match.

## Database additions

```text
curricula
  |
  +-- curriculum_units
  |      |
  |      +-- curriculum_topics (vector embeddings)
  |
  +-- curriculum_questions
  |
  +-- documents (curriculum_id, document_type)
          |
          +-- document_chunks (vector embeddings)
```
