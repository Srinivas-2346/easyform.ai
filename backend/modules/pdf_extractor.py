import pymupdf


MAX_PDF_BYTES = 15 * 1024 * 1024
MAX_PDF_PAGES = 400


class PdfInputError(ValueError):
    pass


def extract_pdf_text(contents: bytes) -> str:
    if not contents:
        raise PdfInputError("The uploaded file is empty.")
    if len(contents) > MAX_PDF_BYTES:
        raise PdfInputError("PDF files must be 15 MB or smaller.")
    if not contents.startswith(b"%PDF-"):
        raise PdfInputError("This file does not appear to be a valid PDF.")

    try:
        with pymupdf.open(stream=contents, filetype="pdf") as document:
            if document.page_count > MAX_PDF_PAGES:
                raise PdfInputError(f"PDF files may contain at most {MAX_PDF_PAGES} pages.")
            text = "\n\n".join(page.get_text("text") for page in document)
    except PdfInputError:
        raise
    except Exception as error:
        raise PdfInputError("We could not read this PDF. Try another copy of the file.") from error

    if not text.strip():
        raise PdfInputError("No selectable text was found. Scanned PDFs need OCR before they can be simplified.")
    return text