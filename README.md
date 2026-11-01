# EasyForm AI – AI-Powered Government Form Simplification and Understanding System

[![Live application](https://img.shields.io/badge/Live%20app-Cloudflare%20Pages-f38020?logo=cloudflare&logoColor=white)](https://easyform-ai.pages.dev/)
[![Backend API](https://img.shields.io/badge/API-Render-46e3b7?logo=render&logoColor=white)](https://easyform-ai-api.onrender.com/api/health)
[![Source code](https://img.shields.io/badge/Source-GitHub-181717?logo=github&logoColor=white)](https://github.com/Srinivas-2346/easyform.ai)

EasyForm AI helps people understand complex government forms and notices by rewriting their instructions in plain English and organizing the details that matter. It is an assistive portfolio project, not legal advice or a substitute for official government guidance.

- **Live application:** [easyform-ai.pages.dev](https://easyform-ai.pages.dev/)
- **Backend health:** [easyform-ai-api.onrender.com/api/health](https://easyform-ai-api.onrender.com/api/health)
- **Repository:** [github.com/Srinivas-2346/easyform.ai](https://github.com/Srinivas-2346/easyform.ai)

## The Problem

Government forms, notices, and application instructions often use dense or formal language. Important requirements can be difficult to find, especially for people who are unfamiliar with government terminology.

## The Solution

EasyForm AI uses Gemini to simplify submitted instructions while keeping key information visible. It returns an explanation, required documents, eligibility conditions, steps, warnings, deadlines and fees, and any unclear information. Source text and automated preservation checks help users review the result, but do not guarantee legal accuracy.

## Main Features

1. Upload a government PDF or paste instructions.
2. Extract selectable PDF text with PyMuPDF.
3. Generate plain-English explanations with the Google Gemini API.
4. Identify required documents.
5. Explain eligibility conditions.
6. Organize step-by-step instructions.
7. Highlight warnings and penalties.
8. Surface deadlines, fees, and amounts.
9. Flag unclear information for human review.
10. Compare source text with the explanation, copy results, and download a report.

PDF uploads are processed in memory and are not saved by this application. Scanned/image-only PDFs require OCR before they can be used. Do not submit sensitive personal or confidential information.

## Screenshots

Screenshots are not included yet. Add genuine desktop and mobile captures here when available; no placeholder images are presented as product screenshots.

| View | Screenshot |
| --- | --- |
| Desktop application | To be added |
| Mobile application | To be added |

## Project Workflow

1. The user pastes text or uploads a PDF from the React interface.
2. FastAPI validates the request. PyMuPDF extracts text from PDFs in memory.
3. Long input is divided into overlapping chunks and sent to Gemini through the official Python SDK.
4. Gemini returns structured fields for the explanation and requirement categories.
5. The backend validates the response and checks for potentially omitted dates, numbers, common document names, and requirements.
6. The frontend displays the source alongside the categorized result and any review flags.

The preservation checks are heuristic and can miss context. Users should verify official requirements with the issuing authority.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, Lucide React |
| Backend | Python, FastAPI, Uvicorn |
| Generative AI | Google Gemini API, official `google-genai` Python SDK |
| PDF processing | PyMuPDF |
| Hosting | Cloudflare Pages (frontend), Render (backend) |
| Version control | Git, GitHub |

## Repository Structure

```text
.
├── backend/
│   ├── main.py                 # FastAPI app and API endpoints
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Local secret template (placeholder only)
│   └── modules/
│       ├── ai_simplifier.py    # Gemini prompt, structured output, chunk orchestration
│       ├── pdf_extractor.py    # PDF validation and PyMuPDF extraction
│       ├── text_processor.py   # Input validation and safe chunking
│       └── validator.py        # Preservation checks and result merging
├── frontend/
│   ├── src/
│   │   ├── services/api.js     # Frontend API client
│   │   ├── App.jsx             # Single-page application
│   │   └── index.css           # Responsive styles
│   ├── .env.example            # Public API URL template
│   └── package.json
├── sample_documents/
│   └── sample_instructions.txt # Fictional test document
├── tests/
│   └── test_backend.py
├── render.yaml                 # Render Blueprint
└── README.md
```

## Local Setup (Windows 11)

Prerequisites: Python 3.11+, Node.js 20+ with npm, and Git. From the project root, create a local environment file and enter your Gemini key in it. The actual `.env` file is ignored by Git; never put the key in frontend code or commit it.

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Add `GEMINI_API_KEY=your_key_here` to the local file, then start the backend in one PowerShell terminal:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload
```

In a second terminal, start the frontend:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://127.0.0.1:5173`). The Vite development server proxies API calls to `http://127.0.0.1:8000`. The app uses in-page anchors and does not require SPA route rewrites.

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Backend health status |
| `POST` | `/api/simplify/text` | Simplify JSON request body containing `text` |
| `POST` | `/api/simplify/pdf` | Extract and simplify multipart PDF field `file` |

Successful simplification responses contain `simple_explanation`, `required_documents`, `eligibility_conditions`, `step_by_step_instructions`, `important_warnings`, `deadlines_and_fees`, and `unclear_information`, plus the original text, source-linked chunks, and preservation-check results.

## Tests and Build

Run from the repository root after installing the backend dependencies and frontend packages:

```powershell
python -m pytest -q
npm --prefix frontend run build
```

The sample in `sample_documents/sample_instructions.txt` is fictional and is not an official form.

## Deployment

The frontend is hosted at Cloudflare Pages and the API at Render. Deployment settings are documented in [render.yaml](render.yaml) and the environment examples. To deploy a new version, follow the dashboard steps in the commit history or configure the hosting projects to build from GitHub.

- Render start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Render environment: `GEMINI_API_KEY` and `CORS_ORIGINS`
- Cloudflare Pages root: `frontend`; build: `npm run build`; output: `dist`
- Cloudflare Pages build variable: `VITE_API_BASE_URL` set to the Render API origin

Render's free web service can sleep after inactivity, which can make the first request slow. Free hosting does not guarantee uninterrupted 24/7 API availability. Gemini free-tier quota and availability depend on Google account, region, and current terms.

## Security and Privacy

- Keep `GEMINI_API_KEY` only in `backend/.env` for local development and in the backend host's secret environment settings for deployment.
- `.env`, virtual environments, `node_modules`, build output, caches, and temporary uploads are excluded by `.gitignore`.
- `.env.example` files contain placeholders only. `VITE_API_BASE_URL` is a public service URL, not a secret.
- Documents are processed for the request and are not stored by the app. Text is sent to Google Gemini for simplification under Google's applicable terms.
- Do not upload sensitive or confidential information. Always verify requirements with the relevant government authority.

## Limitations and Future Work

- Scanned PDFs do not include selectable text; OCR is not currently integrated.
- Automated checks cannot guarantee that every legal requirement is preserved.
- Render's free service may sleep and has platform usage limits.
- Future improvements could include OCR, broader language support, more robust source-to-result alignment, and end-to-end browser tests.