# Resume Tailor

[Try the live app](https://resume-tailor-web-c36c.onrender.com/)

Resume Tailor helps you compare a resume with a job description and prepare
role-specific application materials. Upload a PDF, TXT, or Markdown resume,
paste the job description, and choose what you want: suggestions, a tailored
resume, a cover letter, or any combination. Suggestions can be generated
without a resume.

## How it works

The backend runs one CrewAI agent through a short sequence of tasks. It first
analyzes the job description and, when a resume is provided, looks for supported
matches and gaps. That analysis then informs the optional resume and cover
letter tasks. The agent is instructed not to invent experience or
qualifications, but its output still needs your review.

This is a human-in-the-loop tool: it does not search for jobs, submit
applications, or make hiring decisions.

## Run it locally

The project currently supports Python 3.10–3.13. It uses Gemini through
CrewAI's Google GenAI integration and needs a Google AI Studio API key.

From the project root, create a `.env` file based on `.env.example` and add your
key as `GEMINI_API_KEY`. Keep `.env` private; do not commit it.

In one PowerShell terminal, install and start the API:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m uvicorn resume_tailor.api:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd .\web
npm ci
npm.cmd run dev
```

Open the local URL printed by Vite. Its `/api` requests are proxied to the API.
For deployment settings and more local setup details, see [web/README.md](web/README.md).

## A note on your data

Resume and job-description text is sent to the configured Gemini model. Check
Google's data policy before using personal information, and consider removing
contact details. The public demo does not have sign-in or rate limiting, so avoid uploading sensitive resumes.

## Built with

CrewAI, Gemini, FastAPI, React, TypeScript, and Vite.
