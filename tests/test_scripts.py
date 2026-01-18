"""
test_scripts.py - Tests for PyDebFlow shell scripts and CLI
=============================================================

This module tests the functionality of the scripts in the scripts/ folder
and the pydebflow CLI entry point.
"""

import subprocess
import sys
import os
from pathlib import Path
import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


class TestPyDebFlowCLI:
    """Tests for the pydebflow.py CLI."""
    
    def test_cli_help(self):
        """Test that --help works."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "pydebflow.py"), "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "PyDebFlow" in result.stdout
        assert "simulate" in result.stdout
        assert "gui" in result.stdout
        assert "test" in result.stdout
        assert "info" in result.stdout
    
    def test_cli_version(self):
        """Test that --version works."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "pydebflow.py"), "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout
    
    def test_cli_info(self):
        """Test the info command."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "pydebflow.py"), "info"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "PyDebFlow Information" in result.stdout
        assert "Python:" in result.stdout
        assert "Platform:" in result.stdout
        assert "Dependencies:" in result.stdout
    
    def test_cli_simulate_help(self):
        """Test simulate command help."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "pydebflow.py"), "simulate", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--dem" in result.stdout
        assert "--synthetic" in result.stdout
        assert "--time" in result.stdout
    
    def test_cli_test_help(self):
        """Test test command help."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "pydebflow.py"), "test", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--all" in result.stdout
        assert "--module" in result.stdout
    
    def test_cli_no_args_shows_help(self):
        """Test that running without args shows help/usage."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "pydebflow.py")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Should show quick start or usage
        assert "simulate" in result.stdout or "Quick Start" in result.stdout


class TestScriptsExist:
    """Tests that all required scripts exist."""
    
    @pytest.fixture
    def scripts_dir(self):
        return PROJECT_ROOT / "scripts"
    
    def test_scripts_directory_exists(self, scripts_dir):
        """Test that scripts directory exists."""
        assert scripts_dir.exists()
        assert scripts_dir.is_dir()
    
    def test_install_scripts_exist(self, scripts_dir):
        """Test that install scripts exist."""
        assert (scripts_dir / "install.sh").exists()
        assert (scripts_dir / "install.bat").exists()
    
    def test_run_scripts_exist(self, scripts_dir):
        """Test that run scripts exist."""
        assert (scripts_dir / "run.sh").exists()
        assert (scripts_dir / "run.bat").exists()
    
    def test_test_scripts_exist(self, scripts_dir):
        """Test that test scripts exist."""
        assert (scripts_dir / "test.sh").exists()
        assert (scripts_dir / "test.bat").exists()
    
    def test_build_scripts_exist(self, scripts_dir):
        """Test that build scripts exist."""
        assert (scripts_dir / "build.sh").exists()
        assert (scripts_dir / "build.bat").exists()
    
    def test_pydebflow_wrapper_exists(self, scripts_dir):
        """Test that pydebflow CLI wrapper exists."""
        assert (scripts_dir / "pydebflow").exists()
        assert (scripts_dir / "pydebflow.bat").exists()


class TestWindowsScripts:
    """Tests for Windows batch scripts (on Windows only)."""
    
    @pytest.fixture
    def scripts_dir(self):
        return PROJECT_ROOT / "scripts"
    
    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_run_bat_help(self, scripts_dir):
        """Test run.bat --help on Windows."""
        result = subprocess.run(
            [str(scripts_dir / "run.bat"), "--help"],
            capture_output=True,
            text=True,
            shell=True,
            cwd=str(PROJECT_ROOT)
        )
        # Just check it runs without crashing
        assert "PyDebFlow" in result.stdout or result.returncode == 0
    
    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_test_bat_help(self, scripts_dir):
        """Test test.bat --help on Windows."""
        result = subprocess.run(
            [str(scripts_dir / "test.bat"), "--help"],
            capture_output=True,
            text=True,
            shell=True,
            cwd=str(PROJECT_ROOT)
        )
        assert "--coverage" in result.stdout or result.returncode == 0


class TestBashScriptsSyntax:
    """Tests for bash script syntax (on Unix systems)."""
    
    @pytest.fixture
    def scripts_dir(self):
        return PROJECT_ROOT / "scripts"
    
    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_install_sh_syntax(self, scripts_dir):
        """Test install.sh has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(scripts_dir / "install.sh")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"
    
    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_run_sh_syntax(self, scripts_dir):
        """Test run.sh has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(scripts_dir / "run.sh")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"
    
    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_test_sh_syntax(self, scripts_dir):
        """Test test.sh has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(scripts_dir / "test.sh")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"
    
    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix only")
    def test_build_sh_syntax(self, scripts_dir):
        """Test build.sh has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(scripts_dir / "build.sh")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestScriptContent:
    """Tests for script content and formatting."""
    
    @pytest.fixture
    def scripts_dir(self):
        return PROJECT_ROOT / "scripts"
    
    def test_bash_scripts_have_shebang(self, scripts_dir):
        """Test that bash scripts have proper shebang."""
        bash_scripts = ["install.sh", "run.sh", "test.sh", "build.sh"]
        for script in bash_scripts:
            content = (scripts_dir / script).read_text(encoding='utf-8')
            assert content.startswith("#!/bin/bash"), f"{script} missing shebang"
    
    def test_scripts_have_documentation(self, scripts_dir):
        """Test that scripts have documentation headers."""
        all_scripts = ["install.sh", "run.sh", "test.sh", "build.sh",
                       "install.bat", "run.bat", "test.bat", "build.bat"]
        for script in all_scripts:
            content = (scripts_dir / script).read_text(encoding='utf-8')
            assert "PyDebFlow" in content, f"{script} missing PyDebFlow mention"
            assert "Usage" in content, f"{script} missing usage documentation"


class TestCLIModuleImports:
    """Test that CLI can import all required modules."""
    
    def test_can_import_pydebflow(self):
        """Test that pydebflow module can be imported."""
        # Add project root to path
        sys.path.insert(0, str(PROJECT_ROOT))
        try:
            import pydebflow
            assert hasattr(pydebflow, 'main')
            assert hasattr(pydebflow, 'cmd_simulate')
            assert hasattr(pydebflow, 'cmd_gui')
            assert hasattr(pydebflow, 'cmd_test')
            assert hasattr(pydebflow, 'cmd_info')
        finally:
            sys.path.remove(str(PROJECT_ROOT))
