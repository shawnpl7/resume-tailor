import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from resume_tailor.crew import build_crew


class CrewConfigurationTests(unittest.TestCase):
    def test_builds_single_agent_with_existing_markdown_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with patch.dict(os.environ, {"MODEL": "gemini/gemini-3.6-flash"}):
                crew = build_crew(output_dir)

            self.assertEqual(len(crew.agents), 1)
            self.assertEqual(len(crew.tasks), 3)
            self.assertTrue(all(task.agent is crew.agents[0] for task in crew.tasks))
            self.assertEqual(
                [Path(task.output_file).name for task in crew.tasks],
                ["job_analysis.md", "tailored_resume.md", "cover_letter.md"],
            )
            self.assertTrue(
                all(Path(task.output_file).parent == output_dir for task in crew.tasks)
            )

    def test_suggestions_only_runs_the_analysis_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"MODEL": "gemini/gemini-3.6-flash"}):
                crew = build_crew(Path(temp_dir), {"suggestions"})

            self.assertEqual([task.name for task in crew.tasks], ["analyze_job"])
            self.assertEqual(
                Path(crew.tasks[0].output_file).name,
                "job_analysis.md",
            )

    def test_cover_letter_only_keeps_analysis_internal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with patch.dict(os.environ, {"MODEL": "gemini/gemini-3.6-flash"}):
                crew = build_crew(output_dir, {"cover_letter"})

            self.assertEqual(
                [task.name for task in crew.tasks],
                ["analyze_job", "write_cover_letter"],
            )
            self.assertIsNone(crew.tasks[0].output_file)
            self.assertEqual(len(crew.tasks[1].context), 1)
            self.assertEqual(
                Path(crew.tasks[1].output_file).name,
                "cover_letter.md",
            )


if __name__ == "__main__":
    unittest.main()
