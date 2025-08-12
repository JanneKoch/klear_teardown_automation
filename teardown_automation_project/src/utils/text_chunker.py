import tiktoken

def chunk_text(text, max_tokens=3000):
    # Roughly estimate tokens (1 token ≈ 4 characters)
    max_chars = max_tokens * 4
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) < max_chars:
            current += para + "\n\n"
        else:
            chunks.append(current.strip())
            current = para + "\n\n"
    if current:
        chunks.append(current.strip())
    return chunks

