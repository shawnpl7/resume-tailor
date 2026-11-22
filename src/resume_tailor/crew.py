import os
from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, LLM, Process, Task


CONFIG_DIR = Path(__file__).parent / "config"
DELIVERABLES = {"suggestions", "resume", "cover_letter"}
OUTPUT_FILES = {
    "suggestions": "job_analysis.md",
    "resume": "tailored_resume.md",
    "cover_letter": "cover_letter.md",
}


def _read_config(filename: str) -> dict[str, Any]:
    with (CONFIG_DIR / filename).open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def build_crew(
    output_dir: Path,
    deliverables: set[str] | None = None,
) -> Crew:
    selected = DELIVERABLES if deliverables is None else deliverables
    if not selected or not selected.issubset(DELIVERABLES):
        raise ValueError("Select at least one supported deliverable.")

    agents_config = _read_config("agents.yaml")
    tasks_config = _read_config("tasks.yaml")
    llm = LLM(model=os.getenv("MODEL", "gemini/gemini-3.6-flash"))
    agent = Agent(config=agents_config["resume_tailor"], llm=llm)

    analysis_config = tasks_config["analyze_job"]
    analysis_task = Task(
        name="analyze_job",
        description=analysis_config["description"],
        expected_output=analysis_config["expected_output"],
        agent=agent,
        output_file=(
            str(output_dir / OUTPUT_FILES["suggestions"])
            if "suggestions" in selected
            else None
        ),
    )
    tasks = [analysis_task]

    resume_task: Task | None = None
    if "resume" in selected:
        resume_config = tasks_config["tailor_resume"]
        resume_task = Task(
            name="tailor_resume",
            description=resume_config["description"],
            expected_output=resume_config["expected_output"],
            agent=agent,
            context=[analysis_task],
            output_file=str(output_dir / OUTPUT_FILES["resume"]),
        )
        tasks.append(resume_task)

    if "cover_letter" in selected:
        cover_letter_config = tasks_config["write_cover_letter"]
        cover_letter_context = [analysis_task]
        if resume_task is not None:
            cover_letter_context.append(resume_task)
        tasks.append(
            Task(
                name="write_cover_letter",
                description=cover_letter_config["description"],
                expected_output=cover_letter_config["expected_output"],
                agent=agent,
                context=cover_letter_context,
                output_file=str(output_dir / OUTPUT_FILES["cover_letter"]),
            )
        )

    return Crew(
        agents=[agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
