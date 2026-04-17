"""Tests for interactive CLI Rezzy commands."""

import io

import pytest

from src.client import ResumeCreateResponse, ResumeStatusResponse
from src.cli import _parse_tailor_args, _prompt_job_description, cmd_status, cmd_tailor


class TestCliArgParsing:
    """Validate command argument parsing."""

    def test_parse_tailor_args_basic(self):
        """Parses job id and optional flags."""
        job_id, title, company_url = _parse_tailor_args(
            ["5", "--title", "Backend Intern", "--company-url", "https://example.com"]
        )

        assert job_id == 5
        assert title == "Backend Intern"
        assert company_url == "https://example.com"

    def test_parse_tailor_args_requires_numeric_id(self):
        """Rejects non-numeric job IDs."""
        with pytest.raises(ValueError):
            _parse_tailor_args(["abc"])


class TestCliPrompting:
    """Validate multi-line prompt behavior."""

    def test_prompt_job_description_multiline(self, monkeypatch):
        """Collects lines until END sentinel."""
        import src.cli as cli_module

        monkeypatch.setattr(
            cli_module,
            "sys",
            type("FakeSys", (), {"stdin": io.StringIO("line1\nline2\nEND\n")}),
        )

        result = _prompt_job_description()
        assert result == "line1\nline2"


class TestCliCommands:
    """Validate tailor/status command behavior."""

    def test_cmd_tailor_job_not_found(self, monkeypatch, capsys):
        """tailor reports missing job id cleanly."""
        import src.cli as cli_module

        monkeypatch.setattr(cli_module, "_get_job_by_id", lambda _: None)
        cmd_tailor(["999"])

        output = capsys.readouterr().out
        assert "Job ID 999 not found" in output

    def test_cmd_tailor_uses_job_defaults(self, monkeypatch, capsys, sample_job_posting):
        """tailor uses role/url defaults and calls client."""
        import src.cli as cli_module

        captured = {}

        class FakeClient:
            def create_resume(self, title, job_description, company_url):
                captured["title"] = title
                captured["job_description"] = job_description
                captured["company_url"] = company_url
                return ResumeCreateResponse(
                    id="resume-abc",
                    resume_title=title,
                    status="QUEUED",
                    dashboard_url="https://rezzy.dev/dashboard/resumes",
                )

        monkeypatch.setattr(cli_module, "_get_job_by_id", lambda _: sample_job_posting)
        monkeypatch.setattr(cli_module, "_prompt_job_description", lambda: "JD details")
        monkeypatch.setattr(cli_module, "RezzyClient", FakeClient)

        cmd_tailor(["3"])

        output = capsys.readouterr().out
        assert "Resume job queued successfully" in output
        assert captured["title"] == sample_job_posting.role
        assert captured["company_url"] == sample_job_posting.url
        assert captured["job_description"] == "JD details"

    def test_cmd_tailor_overrides_title_and_url(self, monkeypatch, sample_job_posting):
        """Explicit flags override job defaults."""
        import src.cli as cli_module

        captured = {}

        class FakeClient:
            def create_resume(self, title, job_description, company_url):
                captured["title"] = title
                captured["company_url"] = company_url
                return ResumeCreateResponse(
                    id="resume-abc",
                    resume_title=title,
                    status="QUEUED",
                    dashboard_url=None,
                )

        monkeypatch.setattr(cli_module, "_get_job_by_id", lambda _: sample_job_posting)
        monkeypatch.setattr(cli_module, "_prompt_job_description", lambda: "JD details")
        monkeypatch.setattr(cli_module, "RezzyClient", FakeClient)

        cmd_tailor(
            [
                "3",
                "--title",
                "Custom Title",
                "--company-url",
                "https://custom.example.com",
            ]
        )

        assert captured["title"] == "Custom Title"
        assert captured["company_url"] == "https://custom.example.com"

    def test_cmd_status_usage_validation(self, capsys):
        """status command prints usage for wrong argument count."""
        cmd_status([])

        output = capsys.readouterr().out
        assert "Usage: status <resume_id>" in output

    def test_cmd_status_success(self, monkeypatch, capsys):
        """status prints status details for one resume id."""
        import src.cli as cli_module

        class FakeClient:
            def get_resume_status(self, resume_id):
                assert resume_id == "resume-123"
                return ResumeStatusResponse(
                    id="resume-123",
                    resume_title="Software Engineer Intern",
                    status="SUCCESS",
                    stage="completed",
                    pdf_url="https://storage.example.com/resumes/resume-123.pdf",
                    dashboard_url="https://rezzy.dev/dashboard/resumes",
                )

        monkeypatch.setattr(cli_module, "RezzyClient", FakeClient)
        cmd_status(["resume-123"])

        output = capsys.readouterr().out
        assert "Resume Status" in output
        assert "SUCCESS" in output
        assert "PDF URL" in output
