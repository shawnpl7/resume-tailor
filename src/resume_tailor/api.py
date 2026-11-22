import os
import uuid
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pypdf.errors import PdfReadError

from resume_tailor.crew import OUTPUT_FILES, build_crew
from resume_tailor.main import read_input_content


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_RESUME_SIZE = 10 * 1024 * 1024
MAX_JOB_DESCRIPTION_LENGTH = 100_000
Deliverable = Literal["suggestions", "resume", "cover_letter"]

load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="Resume Tailor")
configured_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("WEB_ORIGIN", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *configured_origins,
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _generate(
    job_description: str,
    resume: str,
    deliverables: set[str],
) -> dict[str, object]:
    run_id = uuid.uuid4().hex
    output_dir = PROJECT_ROOT / "output" / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)

    crew = build_crew(output_dir, deliverables)
    crew.kickoff(inputs={"resume": resume, "job_description": job_description})

    results = {
        deliverable: (output_dir / filename).read_text(encoding="utf-8")
        for deliverable, filename in OUTPUT_FILES.items()
        if deliverable in deliverables
    }
    return {"run_id": run_id, "results": results}


@app.post("/api/generate")
async def generate(
    job_description: str = Form(...),
    deliverables: list[Deliverable] = Form(...),
    resume_file: UploadFile | None = File(default=None),
) -> dict[str, object]:
    job_description = job_description.strip()
    if not job_description:
        raise HTTPException(status_code=400, detail="Add a job description to continue.")
    if len(job_description) > MAX_JOB_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="The job description is too long.")

    selected = set(deliverables)
    if not selected:
        raise HTTPException(status_code=400, detail="Choose at least one result.")

    resume = "Not provided"
    if resume_file is not None:
        filename = Path(resume_file.filename or "").name
        if not filename:
            raise HTTPException(status_code=400, detail="Choose a resume file.")
        content = await resume_file.read(MAX_RESUME_SIZE + 1)
        if len(content) > MAX_RESUME_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Resume files must be 10 MB or smaller.",
            )
        try:
            resume = read_input_content(filename, content, "Resume")
        except (ValueError, UnicodeDecodeError, PdfReadError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            await resume_file.close()
    elif selected.intersection({"resume", "cover_letter"}):
        raise HTTPException(
            status_code=400,
            detail="Upload a resume to generate a tailored resume or cover letter.",
        )

    return await run_in_threadpool(
        _generate,
        job_description,
        resume,
        selected,
    )
