import json
import streamlit as st
from google import genai
from google.genai import types


GENERATION_MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSION = 768


def get_gemini_client():
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"]
        )
    return st.session_state.gemini_client


def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    if not texts:
        return []

    client = get_gemini_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )
    return [item.values for item in response.embeddings]


def generate_text(prompt: str) -> str:
    client = get_gemini_client()
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return (response.text or "").strip()


def generate_json(prompt: str):
    client = get_gemini_client()
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    text = (response.text or "").strip()
    return json.loads(text)
