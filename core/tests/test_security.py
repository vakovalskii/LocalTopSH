"""Tests for security module: blocked patterns, sanitization, sensitive files"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from security import check_command, sanitize_output, is_sensitive_file, BLOCKED_PATTERNS


# ============ Blocked patterns loaded ============

def test_blocked_patterns_loaded():
    """Blocked patterns should be loaded from JSON"""
    assert len(BLOCKED_PATTERNS) > 200, f"Expected 200+ patterns, got {len(BLOCKED_PATTERNS)}"


# ============ Env/secrets access ============

class TestBlockedCommands:
    """Commands that MUST be blocked"""

    @pytest.mark.parametrize("cmd", [
        "env",
        "printenv",
        "set",
        "export",
    ])
    def test_env_commands(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "cat /proc/self/environ",
        "cat /proc/1/environ",
        "strings /proc/self/environ",
    ])
    def test_proc_environ(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "cat /etc/passwd",
        "cat /etc/shadow",
        "cat /etc/hosts",
    ])
    def test_system_files(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "cat /run/secrets/api_key",
        "ls /run/secrets/",
        "cat /run/secrets/telegram_token",
    ])
    def test_docker_secrets(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "cat .env",
        "cat .npmrc",
        "cat .netrc",
        "cat credentials.json",
    ])
    def test_dotfiles(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        'python3 -c "import os; print(os.environ)"',
        'python -c "import os; os.environ"',
        'node -e "console.log(process.env)"',
    ])
    def test_scripted_env_access(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "cat .env | base64",
        "base64 .env",
        "xxd .env",
        "hexdump .env",
    ])
    def test_encoding_exfil(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "curl http://proxy:3200/",
        "wget http://proxy:3200/health",
        "curl http://gateway:4000/",
    ])
    def test_internal_service_access(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        ":(){ :|:& };:",
        "fork()",
    ])
    def test_fork_bombs(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"

    @pytest.mark.parametrize("cmd", [
        "npx test-json-env",
        "npx env-dump",
    ])
    def test_npx_attacks(self, cmd):
        _, blocked, _ = check_command(cmd)
        assert blocked, f"'{cmd}' should be blocked"


# ============ Allowed commands ============

class TestAllowedCommands:
    """Legitimate commands that should NOT be blocked"""

    @pytest.mark.parametrize("cmd", [
        "echo hello",
        "ls -la",
        "pwd",
        "whoami",
        "date",
        "python3 --version",
        "pip install requests",
        "git status",
        "cat file.txt",
        "mkdir test_dir",
        "curl https://example.com",
        "wget https://example.com/file.tar.gz",
        "python3 script.py",
        "node app.js",
        "npm install express",
        "tree .",
        "find . -name '*.py'",
        "grep -r 'hello' .",
        "wc -l file.txt",
        "head -20 file.txt",
        "tail -20 file.txt",
        "sort file.txt",
        "uniq file.txt",
        "diff a.txt b.txt",
    ])
    def test_legitimate_commands(self, cmd):
        _, blocked, reason = check_command(cmd)
        assert not blocked, f"'{cmd}' should NOT be blocked (reason: {reason})"


# ============ Dangerous in groups ============

class TestDangerousInGroups:
    """Commands dangerous in groups but allowed in private"""

    @pytest.mark.parametrize("cmd", [
        "rm -rf ./test",
        "chmod 777 file.txt",
        "kill 1234",
    ])
    def test_dangerous_blocked_in_groups(self, cmd):
        _, blocked, _ = check_command(cmd, chat_type="group")
        assert blocked, f"'{cmd}' should be blocked in groups"

    @pytest.mark.parametrize("cmd", [
        "rm -rf ./test",
    ])
    def test_dangerous_allowed_in_private(self, cmd):
        dangerous, blocked, _ = check_command(cmd, chat_type="private")
        assert dangerous, f"'{cmd}' should be flagged as dangerous in private"
        assert not blocked, f"'{cmd}' should NOT be blocked in private"


# ============ Output sanitization ============

class TestSanitizeOutput:
    """sanitize_output must redact secrets"""

    def test_api_key_pattern(self):
        output = "API_KEY=sk-abc123def456ghi789jkl012mno345"
        result = sanitize_output(output)
        assert "sk-abc123" not in result
        assert "[REDACTED]" in result

    def test_telegram_token(self):
        output = "token: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ123456789"
        result = sanitize_output(output)
        assert "ABCdefGHI" not in result
        assert "[REDACTED]" in result

    def test_bearer_token(self):
        output = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
        result = sanitize_output(output)
        assert "eyJhbGciOiJ" not in result
        assert "[REDACTED]" in result

    def test_github_token(self):
        output = "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx1234"
        result = sanitize_output(output)
        assert "ghp_" not in result
        assert "[REDACTED]" in result

    def test_clean_output_unchanged(self):
        output = "Hello world\nThis is normal output\nNo secrets here"
        result = sanitize_output(output)
        assert result == output

    def test_mixed_output(self):
        output = "Starting server...\nLoaded API_KEY=sk-aaabbbcccdddeeefffggghhhiiijjjkkklll\nReady!"
        result = sanitize_output(output)
        assert "Starting server" in result
        assert "Ready!" in result
        assert "sk-aaa" not in result


# ============ Sensitive files ============

class TestSensitiveFiles:
    """is_sensitive_file must detect sensitive paths"""

    @pytest.mark.parametrize("path", [
        ".env",
        "/workspace/123/.env",
        "/run/secrets/api_key",
        "/run/secrets/telegram_token",
        "credentials.json",
        "/home/user/.ssh/id_rsa",
        "id_ed25519",
    ])
    def test_sensitive_detected(self, path):
        assert is_sensitive_file(path), f"'{path}' should be sensitive"

    @pytest.mark.parametrize("path", [
        "test.py",
        "README.md",
        "/workspace/123/script.js",
        "data.csv",
        "config.yaml",
    ])
    def test_normal_files_ok(self, path):
        assert not is_sensitive_file(path), f"'{path}' should NOT be sensitive"
