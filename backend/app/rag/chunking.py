from typing import List
import re


# Split the text into sentences using common punctuation marks
def _split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?؟۔])\s+", text)
    result = []

    for sentence in sentences:
        # Remove extra whitespace and ignore empty sentences
        if sentence.strip():
            result.append(sentence.strip())

    return result


# Split the text into overlapping chunks for RAG processing
def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[str]:

    # Remove whitespace from the beginning and end of the text
    text = text.strip()

    # Return an empty list if the text is empty
    if not text:
        return []

    # First split the text into sentences
    sentences = _split_into_sentences(text)

    chunks: List[str] = []
    current = ""

    for sentence in sentences:

        # Try adding the current sentence to the existing chunk
        if current:
            candidate = f"{current} {sentence}".strip()
        else:
            candidate = sentence

        # If the chunk is still within the size limit, keep adding text
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        # The current chunk is full, so save it
        if current:
            chunks.append(current)

            # Keep part of the previous chunk for context continuity
            overlap_text = (
                current[-chunk_overlap:]
                if chunk_overlap > 0
                else ""
            )

            # Start the next chunk with the overlap and current sentence
            current = f"{overlap_text} {sentence}"

        else:
            # If a single sentence is larger than chunk_size,
            # split it directly into smaller pieces
            for i in range(0, len(sentence), chunk_size):
                chunks.append(sentence[i: i + chunk_size])

            current = ""

    # Add the remaining text as the final chunk
    if current:
        chunks.append(current)

    return chunks
