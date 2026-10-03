# START HERE — EXISTING INTELLILEARN DEPLOYMENT

Follow this order.

1. **Back up your current GitHub project.**
2. In Supabase SQL Editor, run `sql/upgrade_curriculum.sql`.
3. Copy the files from this package into your project.
4. Keep your own real `.streamlit/secrets.toml` — do not replace it with the example file.
5. Add `APP_URL` to local and Streamlit Cloud secrets if it is not already present.
6. Verify Supabase Reset Password redirect URL/template as described in `README.md`.
7. Run locally: `streamlit run app.py`.
8. Test in this sequence:
   - Login
   - My Syllabus: upload syllabus/question bank
   - My Documents: upload and attach textbook/notes
   - Ask IntelliLearn: test a question that is in PDF
   - Ask IntelliLearn: test an in-syllabus question missing from PDF
   - Click Generate Recommended Answer
   - Generate Syllabus Unit quiz
   - Generate flashcards
   - Generate study plan
9. Push to GitHub and redeploy.

Do not expose Supabase keys or Gemini API keys in screenshots or GitHub.
