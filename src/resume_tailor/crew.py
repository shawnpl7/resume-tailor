import os
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ResumeTailor:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.llm = LLM(model=os.getenv("MODEL", "gemini/gemini-3.6-flash"))

    @agent
    def resume_tailor(self) -> Agent:
        return Agent(
            config=self.agents_config["resume_tailor"],
            llm=self.llm,
        )

    @task
    def analyze_job(self) -> Task:
        config = self.tasks_config["analyze_job"].copy()
        output_file = config.pop("output_file")
        return Task(
            config=config,
            output_file=str(self.output_dir / output_file),
        )

    @task
    def tailor_resume(self) -> Task:
        config = self.tasks_config["tailor_resume"].copy()
        output_file = config.pop("output_file")
        return Task(
            config=config,
            output_file=str(self.output_dir / output_file),
        )

    @task
    def write_cover_letter(self) -> Task:
        config = self.tasks_config["write_cover_letter"].copy()
        output_file = config.pop("output_file")
        return Task(
            config=config,
            output_file=str(self.output_dir / output_file),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def build_crew(output_dir: Path) -> Crew:
    return ResumeTailor(output_dir).crew()
