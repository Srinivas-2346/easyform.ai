import pymupdf
import pytest
from google.genai.errors import ClientError
from fastapi.testclient import TestClient

from backend import main
from backend.modules import ai_simplifier
from backend.modules.ai_simplifier import GeminiServiceError, SimplificationFields, _simplify_chunk
from backend.modules.pdf_extractor import PdfInputError, extract_pdf_text
from backend.modules.text_processor import InputTextError, split_into_chunks, validate_text
from backend.modules.validator import validate_preservation


client = TestClient(main.app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_origins_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://easyform.pages.dev/, https://preview.example.com")
    assert main._get_cors_origins() == ["https://easyform.pages.dev", "https://preview.example.com"]


def test_cors_preflight_allows_local_frontend():
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_simple_text_is_validated_and_key_error_is_friendly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/simplify/text", json={"text": "Bring your form."})
    assert response.status_code == 503
    assert "backend/.env" in response.json()["detail"]


def test_empty_text_is_rejected():
    response = client.post("/api/simplify/text", json={"text": "   "})
    assert response.status_code == 422


def test_text_endpoint_returns_structured_result(monkeypatch):
    expected = {
        "simple_explanation": "Bring the form.",
        "required_documents": [],
        "eligibility_conditions": [],
        "step_by_step_instructions": ["Bring the form."],
        "important_warnings": [],
        "deadlines_and_fees": [],
        "unclear_information": [],
        "original_text": "Bring the form.",
        "source_sections": [],
        "validation": {"passed": True, "flags": [], "disclaimer": "Verify with the authority."},
    }
    monkeypatch.setattr(main, "simplify_document", lambda text: expected)
    response = client.post("/api/simplify/text", json={"text": "Bring the form."})
    assert response.status_code == 200
    assert response.json()["step_by_step_instructions"] == ["Bring the form."]


def test_gemini_failure_maps_to_bad_gateway(monkeypatch):
    def fail(_text):
        raise GeminiServiceError("The AI service could not process this request.")

    monkeypatch.setattr(main, "simplify_document", fail)
    response = client.post("/api/simplify/text", json={"text": "Pay the application fee."})
    assert response.status_code == 502


def test_simplifier_aggregates_chunks_and_keeps_source_links(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class FakeClient:
        def close(self):
            pass

    fields = SimplificationFields(
        simple_explanation="Follow the listed instructions.",
        required_documents=["A completed form"],
        eligibility_conditions=[],
        step_by_step_instructions=["Complete the form."],
        important_warnings=[],
        deadlines_and_fees=[],
        unclear_information=[],
    )
    monkeypatch.setattr(ai_simplifier.genai, "Client", lambda **kwargs: FakeClient())
    monkeypatch.setattr(ai_simplifier, "_simplify_chunk", lambda _client, _text: fields)
    original = "A" * 13_000

    result = ai_simplifier.simplify_document(original)

    assert len(result["source_sections"]) == 2
    assert result["source_sections"][0]["source_text"] == original[:12_000]
    assert result["source_sections"][-1]["source_end"] == len(original)
    assert result["required_documents"] == ["A completed form"]
    assert result["original_text"] == original


def test_pdf_endpoint_rejects_invalid_pdf():
    response = client.post("/api/simplify/pdf", files={"file": ("invalid.pdf", b"not a pdf", "application/pdf")})
    assert response.status_code == 422


def test_pdf_endpoint_rejects_oversized_upload():
    from backend.modules.pdf_extractor import MAX_PDF_BYTES

    response = client.post("/api/simplify/pdf", files={"file": ("large.pdf", b"%PDF-" + b"0" * MAX_PDF_BYTES, "application/pdf")})
    assert response.status_code == 413


def test_complicated_requirements_are_flagged_if_lost():
    source = "Applicants must submit a birth certificate by March 3, 2027. The fee is $45."
    result = validate_preservation(source, {"simple_explanation": "Send your application soon.", "required_documents": []})
    messages = " ".join(flag["message"] for flag in result["flags"])
    assert "March 3, 2027" in messages
    assert "$45" in messages
    assert "birth certificate" in messages
    assert "possible_missing_requirement" in {flag["type"] for flag in result["flags"]}


def test_preserved_documents_eligibility_deadlines_fees_and_warnings():
    source = "Only residents age 18 or older may apply. Submit a passport by 12/31/2027. The fee is $30. Late applications may be denied."
    output = {
        "simple_explanation": "Residents age 18 or older may apply.",
        "required_documents": ["Submit a passport."],
        "eligibility_conditions": ["You must be a resident and at least 18."],
        "step_by_step_instructions": [],
        "important_warnings": ["Late applications may be denied."],
        "deadlines_and_fees": ["Deadline: 12/31/2027. Fee: $30."],
        "unclear_information": [],
    }
    assert validate_preservation(source, output)["passed"]


def test_chunking_overlaps_without_dropping_source_characters():
    source = ("Eligibility rule. " * 1000).strip()
    chunks = split_into_chunks(source, max_chars=400)
    assert len(chunks) > 1
    assert chunks[0].text.startswith(source[:100])
    assert chunks[-1].end == len(source)
    assert all(chunk.start < chunk.end for chunk in chunks)


def test_empty_and_invalid_pdf_are_rejected():
    with pytest.raises(PdfInputError, match="empty"):
        extract_pdf_text(b"")
    with pytest.raises(PdfInputError, match="valid PDF"):
        extract_pdf_text(b"not a pdf")


def test_empty_pdf_is_rejected():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), " ")
    contents = document.tobytes()
    document.close()
    with pytest.raises(PdfInputError, match="No selectable text"):
        extract_pdf_text(contents)


def test_large_pdf_is_rejected():
    with pytest.raises(PdfInputError, match="15 MB"):
        extract_pdf_text(b"%PDF-" + b"0" * (15 * 1024 * 1024))


def test_text_limits_and_missing_documents():
    with pytest.raises(InputTextError):
        validate_text("  ")
    response = client.post("/api/simplify/text", json={"text": "x" * 100_001})
    assert response.status_code == 422


def test_gemini_failure_and_malformed_response_are_reported():
    class BrokenModels:
        def generate_content(self, **kwargs):
            raise OSError("network unavailable")

    class BrokenClient:
        models = BrokenModels()

    with pytest.raises(GeminiServiceError, match="connection"):
        _simplify_chunk(BrokenClient(), "Must provide proof of identity.")

    class MalformedModels:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "not json"})()

    class MalformedClient:
        models = MalformedModels()

    with pytest.raises(GeminiServiceError, match="malformed"):
        _simplify_chunk(MalformedClient(), "Pay $20.")


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (401, "rejected the API key"),
        (400, "rejected the API key"),
        (429, "quota reached"),
    ],
)
def test_gemini_auth_and_quota_errors_are_friendly_and_redacted(status_code, message):
    class FailedModels:
        def generate_content(self, **kwargs):
            provider_status = "API_KEY_INVALID" if status_code == 400 else "FAILED"
            raise ClientError(
                code=status_code,
                response_json={"error": {"message": "sensitive provider response", "status": provider_status}},
            )

    class FailedClient:
        models = FailedModels()

    with pytest.raises(GeminiServiceError, match=message) as error:
        _simplify_chunk(FailedClient(), "Submit the completed form.")
    assert "sensitive provider response" not in str(error.value)


def test_gemini_busy_error_is_temporary_and_friendly():
    class BusyModels:
        def generate_content(self, **kwargs):
            raise ClientError(code=503, response_json={"error": {"message": "provider busy", "status": "UNAVAILABLE"}})

    class BusyClient:
        models = BusyModels()

    with pytest.raises(GeminiServiceError, match="temporarily unavailable"):
        _simplify_chunk(BusyClient(), "Submit the completed form.")


def test_gemini_response_schema_avoids_unsupported_additional_properties():
    assert "additionalProperties" not in SimplificationFields.model_json_schema()