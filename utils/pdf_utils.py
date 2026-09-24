import fitz  # PyMuPDF


def extract_pages(pdf_bytes: bytes, max_pages: int = 100) -> list[dict]:
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_index in range(min(len(document), max_pages)):
        page = document[page_index]
        text = page.get_text("text").strip()
        if text:
            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": text,
                }
            )

    document.close()
    return pages


def chunk_text(
    text: str,
    chunk_words: int = 500,
    overlap_words: int = 80,
) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max(chunk_words - overlap_words, 1)

    for start in range(0, len(words), step):
        chunk = words[start : start + chunk_words]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        if start + chunk_words >= len(words):
            break

    return chunks


def build_page_chunks(pages: list[dict], max_chunks: int = 300) -> list[dict]:
    output = []
    for page in pages:
        page_chunks = chunk_text(page["text"])
        for idx, content in enumerate(page_chunks):
            output.append(
                {
                    "page_number": page["page_number"],
                    "chunk_index": idx,
                    "content": content,
                }
            )
            if len(output) >= max_chunks:
                return output
    return output
