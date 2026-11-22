# Resume Tailor web app

The React and TypeScript interface uses the existing FastAPI and CrewAI
workflow. Start the API and frontend in separate PowerShell terminals.

## 1. Start the API

From the `resume-tailor` directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn resume_tailor.api:app --reload --host 127.0.0.1 --port 8000
```

The API reads the existing `.env` configuration and uses the Gemini model
selected by `MODEL`.

## 2. Start the frontend

From `resume-tailor\web`:

```powershell
npm.cmd run dev
```

Open the local URL printed by Vite. Its `/api` requests are proxied to the API
on port 8000.

Upload a PDF, TXT, or Markdown resume when requesting a tailored resume or
cover letter. Role notes can be generated without a resume. Generated Markdown
files are saved in `output\runs\<run-id>\` and can also be downloaded from the
results panel.

Resume and job-description text is sent to the configured model provider.
Check that provider's data policy before using personal information.

