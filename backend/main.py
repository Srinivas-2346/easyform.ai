from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.modules.ai_simplifier import GeminiConfigurationError, GeminiServiceError, simplify_document
from backend.modules.pdf_extractor import MAX_PDF_BYTES, PdfInputError, extract_pdf_text
from backend.modules.text_processor import InputTextError, validate_text


load_dotenv(Path(__file__).with_name(".env"))


DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def _get_cors_origins(value: str | None = None) -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "") if value is None else value
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    return list(dict.fromkeys(origins)) or DEFAULT_CORS_ORIGINS


app = FastAPI(title="EasyForm AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


def _simplify(text: str) -> dict:
    try:
        return simplify_document(validate_text(text))
    except InputTextError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except GeminiConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except GeminiServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "EasyForm AI"}


@app.post("/api/simplify/text")
def simplify_text(request: TextRequest) -> dict:
    return _simplify(request.text)


@app.post("/api/simplify/pdf")
async def simplify_pdf(file: UploadFile = File(...)) -> dict:
    try:
        if file.content_type not in {"application/pdf", "application/octet-stream"} and not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=415, detail="Upload a PDF file to continue.")
        contents = await file.read(MAX_PDF_BYTES + 1)
    finally:
        await file.close()
    if len(contents) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF files must be 15 MB or smaller.")
    try:
        text = extract_pdf_text(contents)
    except PdfInputError as error:
        status = 413 if "15 MB" in str(error) or "pages" in str(error) else 422
        raise HTTPException(status_code=status, detail=str(error)) from error
    return _simplify(text)