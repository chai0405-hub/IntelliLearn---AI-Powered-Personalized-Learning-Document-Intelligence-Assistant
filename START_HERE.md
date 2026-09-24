# START HERE

Use the files in this exact order.

## A. Files you do NOT edit first

Keep these as provided:

- `app.py`
- `requirements.txt`
- `.gitignore`
- `.streamlit/config.toml`
- `utils/*`
- `pages/*`

## B. First file to RUN, not upload

Open Supabase → SQL Editor and run:

`sql/setup.sql`

## C. First file you CREATE locally

Copy:

`.streamlit/secrets.example.toml`

Rename the copy to:

`.streamlit/secrets.toml`

Put your real Supabase URL, Supabase key and Gemini API key inside it.

## D. Supabase setting you MUST change

Authentication → Email Templates → Confirm signup.

Make the email contain:

`{{ .Token }}`

This is what makes the email show a verification code instead of only a link.

## E. Then run

`pip install -r requirements.txt`

and:

`streamlit run app.py`

## F. Only after local testing

Push the project to GitHub and deploy it on Streamlit Community Cloud.

Never upload `.streamlit/secrets.toml` to GitHub.
