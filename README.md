# IntelliLearn Starter

AI-Powered Personalized Learning & Document Intelligence Assistant.

This starter includes:

- Full name + username + email + password registration
- Email verification code using Supabase Auth
- Username + password login
- Secure per-user PDF storage
- PDF text extraction with PyMuPDF
- Gemini embeddings
- Supabase pgvector semantic retrieval
- RAG chat with page citations
- AI quiz generation
- AI flashcards
- Personalized study planner
- Progress analytics
- Streamlit Community Cloud-ready structure

---

## 1. Requirements

Install:

- Python 3.11 or 3.12
- VS Code
- Git
- GitHub account
- Supabase free account
- Google AI Studio API key

---

## 2. Create the Supabase project

1. Open https://supabase.com/
2. Create a new project.
3. Wait until the project is ready.
4. Open **SQL Editor**.
5. Copy all content from `sql/setup.sql`.
6. Run it once.

This creates:
- profiles
- documents
- document_chunks
- quiz_attempts
- study_plans
- RLS policies
- vector search function
- private `documents` storage bucket

---

## 3. Configure email verification CODE

Supabase normally sends a confirmation link. IntelliLearn is designed for a code entry screen.

In Supabase:

**Authentication → Email Templates → Confirm signup**

Replace the body with something like:

```html
<h2>Verify your IntelliLearn account</h2>
<p>Your verification code is:</p>
<h1>{{ .Token }}</h1>
<p>Enter this code in IntelliLearn to finish registration.</p>
```

Make sure email confirmation remains enabled.

The app verifies this code with `supabase.auth.verify_otp(...)`.

---

## 4. Get Supabase keys

Go to:

**Project Settings → API**

Copy:
- Project URL
- Publishable key (or legacy anon key)

Do **NOT** use the service-role key in this app.

---

## 5. Get Gemini API key

Open Google AI Studio and create an API key.

The starter currently uses:

- Generation: `gemini-3.5-flash-lite`
- Embeddings: `gemini-embedding-2`
- Embedding size: 768

---

## 6. Create your local secrets file

Copy:

`.streamlit/secrets.example.toml`

to:

`.streamlit/secrets.toml`

Then add your real values:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-publishable-or-anon-key"
GEMINI_API_KEY = "your-gemini-api-key"
```

Never push `secrets.toml` to GitHub.

---

## 7. Install packages

Open a terminal in the project folder:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

---

## 8. Run locally

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

Test in this order:

1. Register
2. Check email
3. Enter verification code
4. Login with username + password
5. Upload a text-based PDF
6. Process it
7. Ask a question
8. Generate quiz
9. Generate flashcards
10. Create study plan
11. View progress

---

## 9. Push to GitHub

Create a repository, for example:

`intellilearn-ai`

Then:

```bash
git init
git add .
git commit -m "Initial IntelliLearn MVP"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Check that `.streamlit/secrets.toml` is NOT visible on GitHub.

---

## 10. Deploy to Streamlit Community Cloud

1. Open https://share.streamlit.io/
2. Sign in with GitHub.
3. Choose **Create app**.
4. Select your `intellilearn-ai` repository.
5. Branch: `main`
6. Main file: `app.py`
7. Open **Advanced settings**.
8. Choose Python 3.12.
9. Paste these secrets:

```toml
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
GEMINI_API_KEY = "..."
```

10. Deploy.

You will receive a public URL similar to:

`https://your-intellilearn.streamlit.app`

---

## Important MVP limitations

This starter intentionally keeps the project easy to understand for a final-year CSE team.

- It supports text-based PDFs.
- Scanned-image PDFs require OCR, which can be added later.
- Document processing is synchronous, so use normal-sized PDFs for the demo.
- Free APIs have usage/rate limits.
- For a production-scale system, move long document processing to background jobs and add stronger abuse/rate-limit controls.

---

## Architecture

```text
Student
   |
Streamlit UI
   |
   +-------------------+
   |                   |
Supabase Auth       Gemini API
   |                   |
Postgres            Generation
Storage             Embeddings
pgvector               |
   |                   |
   +------ RAG --------+
```

RAG flow:

```text
PDF Upload
  ↓
PyMuPDF
  ↓
Text Chunks
  ↓
Gemini Embeddings
  ↓
Supabase pgvector
  ↓
Student Question
  ↓
Question Embedding
  ↓
Semantic Search
  ↓
Relevant Chunks
  ↓
Gemini Generation
  ↓
Answer + Page Sources
```
