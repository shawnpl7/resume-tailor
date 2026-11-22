import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from resume_tailor.main import read_input


class ReadInputTests(unittest.TestCase):
    def test_reads_utf8_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.md"
            path.write_text("# Resume\n\nPython developer", encoding="utf-8")

            self.assertEqual(read_input(path, "Resume"), "# Resume\n\nPython developer")

    @patch("resume_tailor.main.PdfReader")
    def test_extracts_text_from_pdf(self, pdf_reader: MagicMock) -> None:
        pdf_reader.return_value = SimpleNamespace(
            is_encrypted=False,
            pages=[
                SimpleNamespace(extract_text=lambda: "First page"),
                SimpleNamespace(extract_text=lambda: "Second page"),
            ],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.PDF"
            path.write_bytes(b"PDF")

            self.assertEqual(
                read_input(path, "Resume"),
                "First page\nSecond page",
            )
        pdf_reader.assert_called_once_with(path)

    @patch("resume_tailor.main.PdfReader")
    def test_rejects_encrypted_pdf(self, pdf_reader: MagicMock) -> None:
        pdf_reader.return_value = SimpleNamespace(is_encrypted=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.pdf"
            path.write_bytes(b"PDF")

            with self.assertRaisesRegex(ValueError, "encrypted"):
                read_input(path, "Resume")

    @patch("resume_tailor.main.PdfReader")
    def test_rejects_pdf_without_extractable_text(
        self, pdf_reader: MagicMock
    ) -> None:
        pdf_reader.return_value = SimpleNamespace(
            is_encrypted=False,
            pages=[SimpleNamespace(extract_text=lambda: None)],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.pdf"
            path.write_bytes(b"PDF")

            with self.assertRaisesRegex(ValueError, "OCR"):
                read_input(path, "Resume")


if __name__ == "__main__":
    unittest.main()
