import argparse
from io import BytesIO, TextIOWrapper
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader

from resume_tailor.crew import build_crew


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_input_content(filename: str, content: bytes, label: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise ValueError(f"{label} must be a PDF, TXT, or Markdown file.")

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise ValueError(f"{label} PDF is encrypted.")
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        if not text:
            raise ValueError(
                f"{label} PDF contains no extractable text. "
                "Scanned PDFs need OCR before they can be used."
            )
    else:
        with TextIOWrapper(BytesIO(content), encoding="utf-8") as text_stream:
            text = text_stream.read().strip()
    if not text:
        raise ValueError(f"{label} file is empty.")
    return text


def read_input(path: Path, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label} file does not exist: {path}")
    return read_input_content(path.name, path.read_bytes(), label)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tailor a resume and draft a cover letter for one job."
    )
    parser.add_argument(
        "--resume",
        required=True,
        type=Path,
        help="Resume file (UTF-8 text, Markdown, or PDF)",
    )
    parser.add_argument(
        "--job-description",
        required=True,
        type=Path,
        help="Job description file (UTF-8 text, Markdown, or PDF)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated Markdown files (default: output)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")

    resume = read_input(args.resume, "Resume")
    job_description = read_input(args.job_description, "Job description")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    crew = build_crew(output_dir)
    crew.kickoff(inputs={"resume": resume, "job_description": job_description})
    print(f"Generated files are in: {output_dir}")


if __name__ == "__main__":
    main()
