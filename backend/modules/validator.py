import re
from collections.abc import Iterable


DATE_PATTERNS = (
    re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:,?\s+\d{4})?\b", re.I),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
)
NUMBER_PATTERN = re.compile(r"(?<!\w)(?:\$\s*)?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|dollars?|USD)?\b", re.I)
REQUIREMENT_PATTERN = re.compile(
    r"\b(must|required|eligible|eligibility|only if|submit|provide|fee|penalty|deadline|due date|shall|cannot|may not)\b",
    re.I,
)
DOCUMENT_PATTERN = re.compile(
    r"\b(?:passport|driver'?s license|birth certificate|proof of (?:identity|residence|income|citizenship)|tax return|photo ID|application form|bank statement|social security card)\b",
    re.I,
)


def _all_output_text(results: dict) -> str:
    values: list[str] = [str(results.get("simple_explanation", ""))]
    for key in (
        "required_documents",
        "eligibility_conditions",
        "step_by_step_instructions",
        "important_warnings",
        "deadlines_and_fees",
        "unclear_information",
    ):
        values.extend(str(value) for value in results.get(key, []))
    return "\n".join(values)


def _matches(pattern: re.Pattern, text: str) -> set[str]:
    return {match.group(0).strip().lower() for match in pattern.finditer(text)}


def validate_preservation(original: str, results: dict) -> dict:
    simplified = _all_output_text(results)
    flags: list[dict[str, str]] = []

    for pattern, label in ((DATE_PATTERNS[0], "date"), (DATE_PATTERNS[1], "date"), (DATE_PATTERNS[2], "date"), (NUMBER_PATTERN, "number or amount")):
        for value in sorted(_matches(pattern, original)):
            if value not in simplified.lower():
                flags.append({"type": "preservation_check", "message": f"Check that this {label} is preserved: {value}"})

    output_lower = simplified.lower()
    for document in sorted(_matches(DOCUMENT_PATTERN, original)):
        if document not in output_lower:
            flags.append({"type": "document_check", "message": f"Check that this document is still required: {document}"})

    for sentence in re.split(r"(?<=[.!?])\s+|\n+", original):
        if REQUIREMENT_PATTERN.search(sentence) and len(sentence.strip()) >= 18:
            keywords = [word.lower() for word in re.findall(r"[A-Za-z]{4,}", sentence) if word.lower() not in {"must", "will", "shall", "required", "provide", "submit", "eligible", "eligibility", "application", "applicant"}]
            if keywords and not any(word in output_lower for word in keywords[:4]):
                excerpt = sentence.strip()[:140]
                flags.append({"type": "possible_missing_requirement", "message": f"Review this source requirement: {excerpt}"})

    for item in results.get("unclear_information", []):
        flags.append({"type": "unclear_information", "message": str(item)})

    unique_flags = list({(flag["type"], flag["message"]): flag for flag in flags}.values())
    return {
        "passed": not unique_flags,
        "flags": unique_flags[:50],
        "disclaimer": "Automated checks can miss context. Verify every requirement with the issuing government authority.",
    }


def merge_unique(values: Iterable[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(str(value).split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            merged.append(cleaned)
    return merged