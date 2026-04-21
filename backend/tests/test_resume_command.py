"""Tests for the resume command."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from src.cli.commands.resume import (
    cmd_resume,
    _load_resume,
    _save_resume,
    _show_resume,
    _update_resume,
    RESUME_FILE_PATH,
)


@pytest.fixture
def temp_resume_file(monkeypatch):
    """Create a temporary resume file and patch RESUME_FILE_PATH."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = Path(tmpdir) / "resume.txt"
        
        # Patch the module-level RESUME_FILE_PATH
        import src.cli.commands.resume as resume_module
        original_path = resume_module.RESUME_FILE_PATH
        resume_module.RESUME_FILE_PATH = temp_file
        
        yield temp_file
        
        # Cleanup
        resume_module.RESUME_FILE_PATH = original_path


@pytest.fixture
def sample_resume_text():
    """Sample resume for testing."""
    return """John Doe
Software Engineer
john@example.com | (613) 555-0123 | github.com/johndoe

SKILLS
Languages: Python, JavaScript, SQL
Tools: Git, Docker, AWS
Frameworks: React, Flask, PostgreSQL

EXPERIENCE
Backend Engineer Intern | TechCorp | Apr 2025 - Aug 2025
- Developed REST APIs using Flask and PostgreSQL
- Wrote unit tests achieving 85% code coverage
- Collaborated with 5 engineers on microservices architecture

EDUCATION
B.Sc. Computer Science | University of Toronto | 2026
GPA: 3.8/4.0
"""


class TestLoadResume:
    """Test _load_resume function."""

    def test_load_resume_file_exists(self, temp_resume_file, sample_resume_text):
        """Test loading resume when file exists."""
        temp_resume_file.write_text(sample_resume_text, encoding="utf-8")
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            result = _load_resume()
            assert result == sample_resume_text

    def test_load_resume_file_not_exists(self, temp_resume_file):
        """Test loading resume when file doesn't exist."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            result = _load_resume()
            assert result is None

    def test_load_resume_encoding_utf8(self, temp_resume_file):
        """Test resume loads correctly with UTF-8 encoding."""
        text_with_unicode = "John Döe\nSkills: Python, C++, français\n"
        temp_resume_file.write_text(text_with_unicode, encoding="utf-8")
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            result = _load_resume()
            assert result == text_with_unicode
            assert "Döe" in result

    def test_load_resume_with_bad_path(self):
        """Test load gracefully handles file that doesn't exist."""
        # This naturally returns None when file doesn't exist
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", Path("/nonexistent/fake.txt")):
            result = _load_resume()
            assert result is None


class TestSaveResume:
    """Test _save_resume function."""

    def test_save_resume_success(self, temp_resume_file, sample_resume_text):
        """Test successful resume save."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            result = _save_resume(sample_resume_text)
            assert result is True
            assert temp_resume_file.read_text() == sample_resume_text

    def test_save_resume_too_short(self, temp_resume_file):
        """Test save fails if resume is too short."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_error") as mock_error:
                result = _save_resume("abc")
                assert result is False
                mock_error.assert_called_once()
                assert "too short" in mock_error.call_args[0][0]

    def test_save_resume_empty_string(self, temp_resume_file):
        """Test save fails with empty string."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_error"):
                result = _save_resume("")
                assert result is False

    def test_save_resume_too_long(self, temp_resume_file):
        """Test save fails if resume exceeds size limit."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            long_text = "a" * 60001  # Exceeds MAX_RESUME_LENGTH
            
            with patch("src.cli.commands.resume.print_error") as mock_error:
                result = _save_resume(long_text)
                assert result is False
                mock_error.assert_called_once()
                assert "too long" in mock_error.call_args[0][0]

    def test_save_resume_write_error_handled(self, temp_resume_file, sample_resume_text):
        """Test save handles write errors gracefully."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("pathlib.Path.write_text", side_effect=IOError("No space left")):
                with patch("src.cli.commands.resume.print_error") as mock_error:
                    result = _save_resume(sample_resume_text)
                    assert result is False
                    mock_error.assert_called_once()

    def test_save_resume_whitespace_only_fails(self, temp_resume_file):
        """Test save fails with whitespace-only content."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_error"):
                result = _save_resume("   \n\n   ")
                assert result is False


class TestShowResume:
    """Test _show_resume function."""

    def test_show_resume_file_exists(self, temp_resume_file, sample_resume_text):
        """Test showing resume when file exists."""
        temp_resume_file.write_text(sample_resume_text, encoding="utf-8")
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_success") as mock_success:
                with patch("src.cli.commands.resume.console.print"):
                    _show_resume()
                    mock_success.assert_called_once_with("Resume displayed above.")

    def test_show_resume_file_not_exists(self, temp_resume_file):
        """Test showing resume when file doesn't exist."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_error") as mock_error:
                with patch("src.cli.commands.resume.print_info") as mock_info:
                    _show_resume()
                    mock_error.assert_called_once_with("No resume set yet.")
                    mock_info.assert_called_once()
                    assert "resume -u" in mock_info.call_args[0][0]


class TestUpdateResume:
    """Test _update_resume function (paste mode)."""

    def test_update_resume_successful_paste(self, temp_resume_file, sample_resume_text):
        """Test successful resume update via paste mode."""
        # Mock readline to return lines, then "END"
        resume_lines = sample_resume_text.split('\n')
        mock_inputs = [line + '\n' for line in resume_lines] + ['END\n', 'y\n']
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("sys.stdin.readline", side_effect=mock_inputs):
                with patch("src.cli.commands.resume.print_success") as mock_success:
                    with patch("src.cli.commands.resume.console.print"):
                        _update_resume()
                        
                        # Check success message
                        mock_success.assert_called_once_with("Resume saved successfully!")
                        
                        # Check file was written
                        assert temp_resume_file.read_text() == sample_resume_text

    def test_update_resume_user_declines(self, temp_resume_file, sample_resume_text):
        """Test abort when user says 'no' at confirmation."""
        # Mock readline to return lines, then "END", then "n\n" for confirmation
        resume_lines = sample_resume_text.split('\n')
        mock_inputs = [line + '\n' for line in resume_lines] + ['END\n', 'n\n']
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("sys.stdin.readline", side_effect=mock_inputs):
                with patch("src.cli.commands.resume.print_info") as mock_info:
                    _update_resume()
                    
                    # Check abort message
                    assert any("Aborted" in str(call) for call in mock_info.call_args_list)
                    
                    # Check file was NOT written
                    assert not temp_resume_file.exists()

    def test_update_resume_empty_input(self, temp_resume_file):
        """Test abort when no input is provided before END."""
        # Just "END" with no actual content
        mock_inputs = ['END\n']
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("sys.stdin.readline", side_effect=mock_inputs):
                with patch("src.cli.commands.resume.print_error") as mock_error:
                    _update_resume()
                    mock_error.assert_called_once()
                    assert "No input" in mock_error.call_args[0][0]

    def test_update_resume_too_short(self, temp_resume_file):
        """Test abort when pasted resume is too short."""
        # Short content then END
        mock_inputs = ['abc\n', 'END\n']
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("sys.stdin.readline", side_effect=mock_inputs):
                with patch("src.cli.commands.resume.print_error") as mock_error:
                    _update_resume()
                    mock_error.assert_called_once()
                    assert "too short" in mock_error.call_args[0][0]

    def test_update_resume_keyboard_interrupt(self, temp_resume_file):
        """Test graceful handling of Ctrl+C."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("sys.stdin.readline", side_effect=KeyboardInterrupt()):
                with patch("src.cli.commands.resume.print_info") as mock_info:
                    _update_resume()
                    
                    # Check abort message
                    assert any("Aborted" in str(call) for call in mock_info.call_args_list)
                    
                    # Check file was NOT written
                    assert not temp_resume_file.exists()

    def test_update_resume_shows_preview(self, temp_resume_file, sample_resume_text):
        """Test that preview is shown before confirmation."""
        # Mock readline with resume lines + END + confirmation
        resume_lines = sample_resume_text.split('\n')
        mock_inputs = [line + '\n' for line in resume_lines] + ['END\n', 'y\n']
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("sys.stdin.readline", side_effect=mock_inputs):
                with patch("src.cli.commands.resume.console.print") as mock_print:
                    _update_resume()
                    
                    # Panel should be printed (contains first 500 chars)
                    assert any(call for call in mock_print.call_args_list)


class TestCmdResume:
    """Test cmd_resume command parsing."""

    def test_cmd_resume_no_args_shows_resume(self, temp_resume_file, sample_resume_text):
        """Test resume command with no args."""
        temp_resume_file.write_text(sample_resume_text, encoding="utf-8")
        
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume._show_resume") as mock_show:
                cmd_resume([])
                mock_show.assert_called_once()

    def test_cmd_resume_update_flag(self, temp_resume_file):
        """Test resume command with -u flag."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume._update_resume") as mock_update:
                cmd_resume(["-u"])
                mock_update.assert_called_once()

    def test_cmd_resume_update_flag_lowercase(self, temp_resume_file):
        """Test resume command with -u flag (lowercase)."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume._update_resume") as mock_update:
                cmd_resume(["-U"])  # Uppercase, should be converted
                mock_update.assert_called_once()

    def test_cmd_resume_invalid_arg(self, temp_resume_file):
        """Test resume command with invalid argument."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_error") as mock_error:
                cmd_resume(["--invalid"])
                mock_error.assert_called_once()
                assert "Invalid argument" in mock_error.call_args[0][0]

    def test_cmd_resume_help_message(self, temp_resume_file):
        """Test that help message is shown for invalid args."""
        with patch("src.cli.commands.resume.RESUME_FILE_PATH", temp_resume_file):
            with patch("src.cli.commands.resume.print_error"):
                with patch("src.cli.commands.resume.print_info") as mock_info:
                    cmd_resume(["--help"])
                    
                    # Help info should be printed
                    help_calls = [str(call) for call in mock_info.call_args_list]
                    assert any("Usage" in call for call in help_calls)
