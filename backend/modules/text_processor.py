from dataclasses import dataclass


MAX_INPUT_CHARS = 100_000
CHUNK_SIZE = 12_000
CHUNK_OVERLAP = 700


class InputTextError(ValueError):
    pass


@dataclass(frozen=True)
class TextChunk:
    number: int
    start: int
    end: int
    text: str


def validate_text(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        raise InputTextError("Add some instructions before simplifying them.")
    if len(normalized) > MAX_INPUT_CHARS:
        raise InputTextError(f"Text must be {MAX_INPUT_CHARS:,} characters or fewer.")
    return normalized


def split_into_chunks(text: str, max_chars: int = CHUNK_SIZE) -> list[TextChunk]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if len(text) <= max_chars:
        return [TextChunk(number=1, start=0, end=len(text), text=text)]

    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = max(
                text.rfind("\n\n", start + max_chars // 2, end),
                text.rfind("\n", start + max_chars // 2, end),
                text.rfind(" ", start + max_chars // 2, end),
            )
            if boundary > start:
                end = boundary
        if end <= start:
            end = min(start + max_chars, len(text))

        chunks.append(TextChunk(number=len(chunks) + 1, start=start, end=end, text=text[start:end]))
        if end == len(text):
            break
        overlap = min(CHUNK_OVERLAP, max_chars // 10)
        start = max(start + 1, end - overlap)

    return chunks