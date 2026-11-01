# EasyForm AI

EasyForm AI turns complex government-form instructions into plain-language explanations while keeping eligibility rules, required documents, dates, fees, warnings, and action steps visible. It is an assistive student project, not legal advice or a replacement for the issuing authority.

## Features

- Paste instructions or upload a text-based PDF (up to 15 MB and 400 pages).
- Extract PDF text in memory with PyMuPDF; scanned/image-only PDFs need OCR first.
- Send bounded chunks to Google Gemini while retaining each source passage beside its result.
- Review a source comparison, six categorized result groups, preservation-check flags, copy output, and a downloadable report.
- No database and no permanent document storage. Avoid submitting sensitive or confidential information.

## Requirements

- Windows 11 (Windows 10 also works)
- Python 3.11 or newer
- Node.js 20 or newer with npm
- Git
- A Gemini API key from Google AI Studio

The frontend is a Cloudflare Pages static site. The API is a Render web service. Gemini availability and free quota depend on Google's current terms and your account. Render's free web service sleeps after 15 minutes without traffic and may take about a minute to wake. Free hosting therefore does not guarantee uninterrupted 24/7 API availability. Render's free filesystem is ephemeral; this app does not rely on it for document storage.

## Local Development

Open two PowerShell terminals in the project root (`EasyForm-AI`).

### Backend

Create the local secret file once, then add your Gemini key in Notepad. Never paste the key into source code or commit `backend/.env`.

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Add the key as `GEMINI_API_KEY=your_key_here`, then run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload
```

If PowerShell blocks virtual-environment activation, run the commands using `.venv\Scripts\python.exe` instead. The API is at `http://127.0.0.1:8000`; health check: `http://127.0.0.1:8000/api/health`.

### Frontend

In the second terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://127.0.0.1:5173`). During local development, Vite proxies `/api` to the local backend. Keep both terminals running. There is no client-side router; the navigation uses page anchors.

### Local tests

From the project root:

```powershell
python -m pytest -q
npm --prefix frontend run build
```

Use `sample_documents/sample_instructions.txt` for a fictional test document. It is not an official form.

## Deploy Manually

No deployment has been run for you. The repository contains [render.yaml](render.yaml), but you must create the accounts, connect the repository, enter secrets, and launch the services yourself.

### 1. Prepare and push to GitHub

Create a new repository on GitHub. It can be private; the deployed website can still be public. From a PowerShell terminal in the project root, inspect the files first. The ignored local key should not appear as an ordinary untracked/staged file.

```powershell
git status --short --ignored
git remote -v
```

For a new repository with no existing remote, replace the URL below with your GitHub repository URL:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git branch -M main
git add .
git status --short
git diff --cached --name-only
```

Confirm `backend/.env` is not in the staged file list. Then, when ready, commit and push:

```powershell
git commit -m "Prepare EasyForm AI for deployment"
git push -u origin main
```

If `git remote -v` already shows the intended repository, do not add a second `origin`. Never use `git add -f` on `.env` files.

### 2. Create the Render backend

1. Create/sign in to a Render account and choose **New → Blueprint**.
2. Connect GitHub and select this repository. Render reads `render.yaml` at the repository root. Confirm the service plan is **Free**.
3. The configuration installs `backend/requirements.txt`, starts `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, and checks `/api/health`. Automatic deploys are disabled in the Blueprint.
4. In Render's Environment settings, enter these values manually:

   - `GEMINI_API_KEY`: your Gemini key. Enter it only in Render's dashboard; do not add it to GitHub, Cloudflare, or this repository.
   - `CORS_ORIGINS`: the exact Cloudflare Pages origin, such as `https://YOUR-PROJECT.pages.dev`. Add custom domains as comma-separated origins, without paths or trailing slashes.

   You can create the Render service first with a temporary CORS origin, then replace it after you know the Pages URL. Render injects `$PORT` at runtime; do not set it yourself.
5. Manually deploy from Render when its environment is configured. Copy the service URL, for example `https://easyform-ai-api.onrender.com`.

Check `https://YOUR-RENDER-SERVICE.onrender.com/api/health`. A free service can sleep after 15 idle minutes, so the first request after inactivity may be slow. The free instance can also be suspended if platform usage limits are exceeded; monitor Render's usage page and do not select a paid plan.

### 3. Create the Cloudflare Pages frontend

1. Create/sign in to Cloudflare and open **Workers & Pages → Create → Pages → Connect to Git**.
2. Select the same GitHub repository.
3. Configure the build:

   - Root directory: `frontend`
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Framework preset: Vite (or configure the values above directly)

4. In the Pages project's **Settings → Environment variables**, add this variable for the production environment:

   - `VITE_API_BASE_URL`: the Render service origin, such as `https://easyform-ai-api.onrender.com`, with no trailing slash. This is a public URL, not a secret.

5. Save and manually trigger a production build/deploy. The Vite build embeds this public API origin into the frontend bundle, so rebuild after changing it.
6. Copy the assigned Pages domain, then return to Render and set `CORS_ORIGINS` to that exact origin (and any custom domain origins, comma-separated). Save the environment change and manually redeploy/restart the backend.

Cloudflare Pages Git integration may build future commits automatically according to its project settings. Review those settings and choose manual deployments if you want every release to require a dashboard action.

### 4. Verify the deployed application

1. Open `https://YOUR-RENDER-SERVICE.onrender.com/api/health` and confirm it returns `{"status":"ok","service":"EasyForm AI"}`.
2. Open the Cloudflare Pages URL and paste the fictional instructions from `sample_documents/sample_instructions.txt`. Confirm the categorized results appear.
3. Upload a small, text-based PDF and confirm the same result flow works. Scanned PDFs require OCR before upload.
4. Test **Copy all** and **Download PDF**.
5. If the browser reports a CORS error, verify the Render `CORS_ORIGINS` value exactly matches the Pages origin (scheme and hostname, no path), then restart/redeploy the backend.
6. If Gemini returns an authentication, quota, or availability message, check the `GEMINI_API_KEY` and account quota in Render and Google AI Studio. Never put the key into frontend variables.

## Configuration Files

- `render.yaml`: free Render service, install/start commands, health check, and manually supplied environment variables.
- `frontend/.env.example`: placeholder `VITE_API_BASE_URL` for local reference; set the actual value in Cloudflare Pages.
- `backend/.env.example`: placeholder for local development only. The real local `backend/.env` is ignored by Git.
- `CORS_ORIGINS`: comma-separated allowed browser origins, configured in Render.
- `GEMINI_API_KEY`: configured in Render's environment settings for deployment; local development reads `backend/.env`.

## API

- `GET /api/health`
- `POST /api/simplify/text` with JSON `{"text":"..."}`
- `POST /api/simplify/pdf` with multipart field `file`

The response contains the seven structured simplification fields, original text, source-linked chunk results, and heuristic preservation flags. Automated checks cannot guarantee legal accuracy. Verify deadlines, fees, eligibility, and required documents with the issuing government authority.

PDF bytes are processed in memory and the upload stream is closed after processing. Document content is not logged or stored by the app; text is sent to Google Gemini for simplification under Google's applicable terms. Do not upload sensitive personal or confidential information.