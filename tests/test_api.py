import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from resume_tailor.api import app


class GenerateEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_cors_allows_local_vite_origin(self) -> None:
        response = self.client.options(
            "/api/generate",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )

    def test_cors_rejects_unconfigured_origin(self) -> None:
        response = self.client.options(
            "/api/generate",
            headers={
                "Origin": "https://unconfigured.example",
                "Access-Control-Request-Method": "POST",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    @patch("resume_tailor.api._generate")
    def test_suggestions_can_run_without_a_resume(self, generate: MagicMock) -> None:
        generate.return_value = {
            "run_id": "test-run",
            "results": {"suggestions": "# Role notes"},
        }

        response = self.client.post(
            "/api/generate",
            data={
                "job_description": "A software engineer role",
                "deliverables": "suggestions",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["suggestions"], "# Role notes")
        self.assertEqual(generate.call_args.args[1], "Not provided")

    @patch("resume_tailor.api._generate")
    def test_resume_deliverable_requires_an_upload(self, generate: MagicMock) -> None:
        response = self.client.post(
            "/api/generate",
            data={
                "job_description": "A software engineer role",
                "deliverables": "resume",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Upload a resume", response.json()["detail"])
        generate.assert_not_called()

    @patch("resume_tailor.api._generate")
    def test_text_resume_is_extracted_before_generation(
        self, generate: MagicMock
    ) -> None:
        generate.return_value = {
            "run_id": "test-run",
            "results": {"cover_letter": "# Cover letter"},
        }

        response = self.client.post(
            "/api/generate",
            data={
                "job_description": "A software engineer role",
                "deliverables": "cover_letter",
            },
            files={
                "resume_file": (
                    "resume.txt",
                    b"Python engineer with API experience",
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            generate.call_args.args[1],
            "Python engineer with API experience",
        )

    @patch("resume_tailor.api._generate")
    def test_multiple_deliverables_are_passed_to_generation(
        self, generate: MagicMock
    ) -> None:
        generate.return_value = {
            "run_id": "test-run",
            "results": {
                "suggestions": "# Role notes",
                "resume": "# Tailored resume",
            },
        }

        response = self.client.post(
            "/api/generate",
            data={
                "job_description": "A software engineer role",
                "deliverables": ["suggestions", "resume"],
            },
            files={
                "resume_file": (
                    "resume.md",
                    b"Python engineer",
                    "text/markdown",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            generate.call_args.args[2],
            {"suggestions", "resume"},
        )


if __name__ == "__main__":
    unittest.main()
