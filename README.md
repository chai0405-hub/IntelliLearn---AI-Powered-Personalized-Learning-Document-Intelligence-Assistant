# IntelliLearn — Curriculum Intelligence Edition

**AI-Powered Personalized Learning & Document Intelligence Assistant**

This package keeps the existing IntelliLearn features and adds the new faculty-requested workflow:

- Registration, email OTP verification and username/password login
- Forgot Password with registered-email reset link
- Syllabus and/or Question Bank upload
- Automatic Subject -> Unit/Module -> Topic extraction
- Semantic curriculum-topic embeddings
- Textbook / Notes / Reference PDF upload linked to a curriculum
- Document-only RAG with page references
- All-materials RAG across a curriculum
- Syllabus-Aware question mapping
- Safe fallback when an answer is missing from the PDF
- **Generate Recommended Answer** using clearly labelled Syllabus-Guided AI
- Document-grounded Quiz generation
- Unit-wise syllabus quiz generation using attached study material
- Document and syllabus-unit flashcards
- Curriculum-aware study planning
- Quiz progress analytics

Read `BLUEPRINT.md` for the full working cycle.

---

## IMPORTANT — Existing deployed project

If your IntelliLearn is already deployed and your original Supabase tables already exist, do **not** delete them.

### Step 1 — Run the upgrade SQL

Open:

**Supabase -> SQL Editor -> New query**

Run:

`sql/upgrade_curriculum.sql`

This adds:

- `curricula`
- `curriculum_units`
- `curriculum_topics`
- `curriculum_questions`
- `documents.document_type`
- `documents.curriculum_id`
- curriculum topic semantic search RPC
- curriculum-wide document semantic search RPC

Your existing users, documents, quizzes and study plans remain in place.

For a completely new Supabase project, run `sql/setup.sql` instead.

---

## Step 2 — Secrets

Keep your real secrets only in:

`.streamlit/secrets.toml`

Use this structure:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-publishable-or-anon-key"
GEMINI_API_KEY = "your-gemini-api-key"
APP_URL = "https://intellilearn-0405.streamlit.app/"
```

Do **not** commit the real secrets file to GitHub.

---

## Step 3 — Supabase email templates

### Confirm signup OTP

Supabase -> Authentication -> Email Templates -> Confirm signup

Make sure the template includes:

```html
<h2>Verify your IntelliLearn account</h2>
<p>Your verification code is:</p>
<h1>{{ .Token }}</h1>
```

### Reset Password

Supabase -> Authentication -> URL Configuration

Add your Streamlit app URL, for example:

```text
https://intellilearn-0405.streamlit.app/**
```

Then Authentication -> Email Templates -> Reset Password, use a recovery link that returns the token hash to the app:

```html
<h2>Reset your IntelliLearn password</h2>
<p>Click below to create a new password.</p>
<p>
  <a href="{{ .RedirectTo }}?token_hash={{ .TokenHash }}&type=recovery">
    Reset Password
  </a>
</p>
```

---

## Step 4 — Install and run

Python 3.11/3.12 is recommended.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

---

# Recommended demo flow

## A. Account

1. Create account
2. Verify email code
3. Sign in
4. Optionally test Forgot Password

## B. Curriculum Intelligence

Open **My Syllabus**.

Upload either:

- Syllabus only
- Question Bank only
- Both syllabus + question bank

Best demo: upload both.

IntelliLearn extracts the official unit/topic structure from the syllabus. If only a question bank is uploaded and no unit labels exist, the structure is explicitly marked **inferred**, not official.

## C. Study material

Open **My Documents**.

Choose:

- Textbook
- Notes
- Reference Material

Attach it to the curriculum created above and process it.

## D. Ask IntelliLearn

Three modes are available:

1. **Document Only** — search one selected PDF.
2. **All My Materials** — search every study PDF attached to the curriculum.
3. **Syllabus-Aware** — search study materials and map the question to a syllabus/question-bank topic.

### If the answer exists in the PDF

The app generates a source-grounded answer with source pages.

### If the PDF does not contain enough information

If the question strongly matches the curriculum, the app shows:

**Generate Recommended Answer**

Only after the student clicks it does Gemini generate a general-knowledge explanation. It is labelled:

**Syllabus-Guided AI — not taken from the uploaded PDF**

No fake textbook page citation is generated.

### If the question is outside the curriculum

The app does not automatically generate a syllabus-guided answer.

---

# Quiz behavior

### Document Only

Quiz facts come only from the selected PDF.

### Syllabus Unit

- Select curriculum
- Select Unit/Module
- Question-bank items may guide exam style/priority
- Factual question content still comes only from the attached textbook/notes context
- If insufficient reliable material exists, the system returns fewer questions instead of inventing facts

---

# Current technical architecture

```text
Streamlit UI
   |
   +--> Supabase Auth
   |      - signup / OTP
   |      - login
   |      - forgot password
   |
   +--> Supabase PostgreSQL + pgvector
   |      - curricula
   |      - units
   |      - topics + embeddings
   |      - question-bank questions
   |      - documents + chunks + embeddings
   |      - quizzes / study plans
   |
   +--> Supabase Storage
   |      - syllabus PDFs
   |      - question-bank PDFs
   |      - textbook / notes PDFs
   |
   +--> Gemini API
          - curriculum extraction
          - embeddings
          - RAG answers
          - context-sufficiency check
          - recommended syllabus-guided answer
          - quiz / flashcards / study plan
```

---

# Important limitations

- Text-based PDFs work directly. Image-only scanned PDFs require OCR, which is not included yet.
- Semantic syllabus matching uses a configurable similarity threshold and should be evaluated with your university syllabus examples.
- Gemini and Supabase free tiers have rate/usage limits.
- This is a final-year-project implementation, not a production LMS.
- AI fallback answers are deliberately labelled separately from document-grounded answers.

---

# Deployment

After testing locally:

```bash
git add .
git commit -m "Add curriculum intelligence and syllabus-aware RAG"
git push
```

Streamlit Community Cloud should redeploy automatically.

If it does not, open your Streamlit app dashboard and reboot/redeploy the app.
