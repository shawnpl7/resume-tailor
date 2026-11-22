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


if __name__ == "__main__":
    unittest.main()
