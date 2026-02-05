"""Tests for all tools via direct execution"""

import sys
import os

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from models import ToolResult, ToolContext
from tools import execute_tool

# Test workspace (isolated)
TEST_DIR = "/tmp/test_workspace/12345"
TEST_CTX = ToolContext(
    cwd=TEST_DIR,
    session_id="test_session",
    user_id=12345,
    chat_id=12345,
    chat_type="private",
    source="bot",
)


@pytest.fixture(scope="module", autouse=True)
def setup_workspace():
    """Create test workspace"""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    # Cleanup
    import shutil
    shutil.rmtree("/tmp/test_workspace", ignore_errors=True)


# ============ run_command ============

@pytest.mark.asyncio
async def test_run_command_echo():
    """run_command: basic echo"""
    r = await execute_tool("run_command", {"command": "echo hello"}, TEST_CTX)
    assert r.success
    assert "hello" in r.output


@pytest.mark.asyncio
async def test_run_command_empty():
    """run_command: empty command returns error"""
    r = await execute_tool("run_command", {"command": ""}, TEST_CTX)
    assert not r.success


@pytest.mark.asyncio
async def test_run_command_exit_code():
    """run_command: failed command returns error"""
    r = await execute_tool("run_command", {"command": "ls /nonexistent_dir_xyz"}, TEST_CTX)
    assert not r.success


@pytest.mark.asyncio
async def test_run_command_multiline():
    """run_command: multiline output"""
    r = await execute_tool("run_command", {"command": "echo 'a\nb\nc'"}, TEST_CTX)
    assert r.success
    assert "a" in r.output


@pytest.mark.asyncio
async def test_run_command_pipe():
    """run_command: pipes work"""
    r = await execute_tool("run_command", {"command": "echo hello world | wc -w"}, TEST_CTX)
    assert r.success
    assert "2" in r.output


# ============ write_file ============

@pytest.mark.asyncio
async def test_write_file_basic():
    """write_file: create file"""
    r = await execute_tool("write_file", {
        "path": "test.txt",
        "content": "hello world"
    }, TEST_CTX)
    assert r.success
    assert os.path.exists(os.path.join(TEST_DIR, "test.txt"))


@pytest.mark.asyncio
async def test_write_file_nested():
    """write_file: creates directories"""
    r = await execute_tool("write_file", {
        "path": "subdir/nested/file.txt",
        "content": "nested content"
    }, TEST_CTX)
    assert r.success
    assert os.path.exists(os.path.join(TEST_DIR, "subdir/nested/file.txt"))


@pytest.mark.asyncio
async def test_write_file_sensitive():
    """write_file: blocks sensitive files"""
    r = await execute_tool("write_file", {
        "path": ".env",
        "content": "SECRET=bad"
    }, TEST_CTX)
    assert not r.success
    assert "sensitive" in r.error.lower() or "🚫" in r.error


# ============ read_file ============

@pytest.mark.asyncio
async def test_read_file_basic():
    """read_file: reads created file"""
    # Write first
    await execute_tool("write_file", {"path": "read_test.txt", "content": "read me"}, TEST_CTX)
    
    r = await execute_tool("read_file", {"path": "read_test.txt"}, TEST_CTX)
    assert r.success
    assert "read me" in r.output


@pytest.mark.asyncio
async def test_read_file_not_found():
    """read_file: returns error for missing file"""
    r = await execute_tool("read_file", {"path": "nonexistent_xyz.txt"}, TEST_CTX)
    assert not r.success
    assert "not found" in r.error.lower()


@pytest.mark.asyncio
async def test_read_file_with_offset():
    """read_file: offset and limit work"""
    content = "\n".join(f"line {i}" for i in range(1, 11))
    await execute_tool("write_file", {"path": "lines.txt", "content": content}, TEST_CTX)
    
    r = await execute_tool("read_file", {"path": "lines.txt", "offset": 3, "limit": 2}, TEST_CTX)
    assert r.success
    assert "line 3" in r.output
    assert "line 5" not in r.output


@pytest.mark.asyncio
async def test_read_file_sensitive():
    """read_file: blocks sensitive files"""
    r = await execute_tool("read_file", {"path": "/run/secrets/api_key"}, TEST_CTX)
    assert not r.success


# ============ edit_file ============

@pytest.mark.asyncio
async def test_edit_file_basic():
    """edit_file: find and replace"""
    await execute_tool("write_file", {"path": "edit_test.txt", "content": "hello world"}, TEST_CTX)
    
    r = await execute_tool("edit_file", {
        "path": "edit_test.txt",
        "old_text": "world",
        "new_text": "python"
    }, TEST_CTX)
    assert r.success
    
    # Verify
    r2 = await execute_tool("read_file", {"path": "edit_test.txt"}, TEST_CTX)
    assert "hello python" in r2.output


@pytest.mark.asyncio
async def test_edit_file_not_found_text():
    """edit_file: old_text not in file"""
    await execute_tool("write_file", {"path": "edit_miss.txt", "content": "abc"}, TEST_CTX)
    
    r = await execute_tool("edit_file", {
        "path": "edit_miss.txt",
        "old_text": "xyz",
        "new_text": "123"
    }, TEST_CTX)
    assert not r.success
    assert "not found" in r.error.lower()


# ============ delete_file ============

@pytest.mark.asyncio
async def test_delete_file_basic():
    """delete_file: removes file"""
    await execute_tool("write_file", {"path": "to_delete.txt", "content": "bye"}, TEST_CTX)
    
    r = await execute_tool("delete_file", {"path": "to_delete.txt"}, TEST_CTX)
    assert r.success
    assert not os.path.exists(os.path.join(TEST_DIR, "to_delete.txt"))


@pytest.mark.asyncio
async def test_delete_file_not_found():
    """delete_file: missing file returns error"""
    r = await execute_tool("delete_file", {"path": "ghost.txt"}, TEST_CTX)
    assert not r.success


# ============ search_files ============

@pytest.mark.asyncio
async def test_search_files_glob():
    """search_files: finds by pattern"""
    await execute_tool("write_file", {"path": "search_a.py", "content": "# a"}, TEST_CTX)
    await execute_tool("write_file", {"path": "search_b.py", "content": "# b"}, TEST_CTX)
    
    r = await execute_tool("search_files", {"pattern": "*.py"}, TEST_CTX)
    assert r.success
    assert "search_a.py" in r.output
    assert "search_b.py" in r.output


@pytest.mark.asyncio
async def test_search_files_no_match():
    """search_files: no match returns empty"""
    r = await execute_tool("search_files", {"pattern": "*.nonexistent"}, TEST_CTX)
    assert r.success
    assert "no match" in r.output.lower()


# ============ search_text ============

@pytest.mark.asyncio
async def test_search_text_grep():
    """search_text: finds text in files"""
    await execute_tool("write_file", {"path": "grep_test.txt", "content": "foo bar baz"}, TEST_CTX)
    
    r = await execute_tool("search_text", {"pattern": "bar", "path": TEST_DIR}, TEST_CTX)
    assert r.success
    assert "bar" in r.output


@pytest.mark.asyncio
async def test_search_text_no_match():
    """search_text: no match returns empty"""
    r = await execute_tool("search_text", {"pattern": "zzz_unique_xxx"}, TEST_CTX)
    assert r.success
    assert "no match" in r.output.lower()


# ============ list_directory ============

@pytest.mark.asyncio
async def test_list_directory():
    """list_directory: shows files"""
    await execute_tool("write_file", {"path": "list_test.txt", "content": "x"}, TEST_CTX)
    
    r = await execute_tool("list_directory", {"path": "."}, TEST_CTX)
    assert r.success
    assert "list_test.txt" in r.output


@pytest.mark.asyncio
async def test_list_directory_workspace_root_blocked():
    """list_directory: blocks workspace root"""
    r = await execute_tool("list_directory", {"path": "/workspace"}, TEST_CTX)
    assert not r.success


# ============ memory ============

@pytest.mark.asyncio
async def test_memory_lifecycle():
    """memory: append, read, clear"""
    # Clear
    await execute_tool("memory", {"action": "clear"}, TEST_CTX)
    
    # Append
    r = await execute_tool("memory", {"action": "append", "content": "Test note 123"}, TEST_CTX)
    assert r.success
    
    # Read
    r = await execute_tool("memory", {"action": "read"}, TEST_CTX)
    assert r.success
    assert "Test note 123" in r.output
    
    # Clear
    r = await execute_tool("memory", {"action": "clear"}, TEST_CTX)
    assert r.success
    
    # Read again - should be empty
    r = await execute_tool("memory", {"action": "read"}, TEST_CTX)
    assert r.success
    assert "Test note 123" not in r.output


@pytest.mark.asyncio
async def test_memory_append_empty():
    """memory: append without content fails"""
    r = await execute_tool("memory", {"action": "append", "content": ""}, TEST_CTX)
    assert not r.success


# ============ manage_tasks ============

@pytest.mark.asyncio
async def test_tasks_lifecycle():
    """manage_tasks: add, list, update, clear"""
    # Clear
    await execute_tool("manage_tasks", {"action": "clear"}, TEST_CTX)
    
    # Add
    r = await execute_tool("manage_tasks", {"action": "add", "content": "Task one"}, TEST_CTX)
    assert r.success
    assert "t1" in r.output.lower() or "task" in r.output.lower()
    
    # Add another
    r = await execute_tool("manage_tasks", {"action": "add", "content": "Task two"}, TEST_CTX)
    assert r.success
    
    # List
    r = await execute_tool("manage_tasks", {"action": "list"}, TEST_CTX)
    assert r.success
    assert "Task one" in r.output
    assert "Task two" in r.output
    assert "pending" in r.output.lower()
    
    # Update
    r = await execute_tool("manage_tasks", {"action": "update", "id": "t1", "status": "done"}, TEST_CTX)
    assert r.success
    
    # Clear
    r = await execute_tool("manage_tasks", {"action": "clear"}, TEST_CTX)
    assert r.success
    
    # List empty
    r = await execute_tool("manage_tasks", {"action": "list"}, TEST_CTX)
    assert r.success
    assert "no task" in r.output.lower()


# ============ schedule_task ============

@pytest.mark.asyncio
async def test_schedule_task_add_list_cancel():
    """schedule_task: add, list, cancel"""
    # Add
    r = await execute_tool("schedule_task", {
        "action": "add",
        "type": "message",
        "content": "Test reminder",
        "delay_minutes": 999,
    }, TEST_CTX)
    assert r.success
    assert "task_" in r.output.lower() or "scheduled" in r.output.lower()
    
    # Extract task_id
    import re
    match = re.search(r"(task_\w+)", r.output)
    assert match, f"No task_id in output: {r.output}"
    task_id = match.group(1)
    
    # List
    r = await execute_tool("schedule_task", {"action": "list"}, TEST_CTX)
    assert r.success
    assert task_id in r.output
    
    # Cancel
    r = await execute_tool("schedule_task", {"action": "cancel", "task_id": task_id}, TEST_CTX)
    assert r.success
    
    # List again - should be empty
    r = await execute_tool("schedule_task", {"action": "list"}, TEST_CTX)
    assert r.success
    assert task_id not in r.output


@pytest.mark.asyncio
async def test_schedule_task_missing_fields():
    """schedule_task: add without required fields fails"""
    r = await execute_tool("schedule_task", {"action": "add"}, TEST_CTX)
    assert not r.success


# ============ search_web ============

@pytest.mark.asyncio
async def test_search_web():
    """search_web: returns results (needs proxy)"""
    r = await execute_tool("search_web", {"query": "python programming"}, TEST_CTX)
    # Might fail if proxy not configured in test context
    # Just check it doesn't crash
    assert isinstance(r, ToolResult)


# ============ fetch_page ============

@pytest.mark.asyncio
async def test_fetch_page_blocked_internal():
    """fetch_page: blocks internal URLs"""
    for url in ["http://localhost/", "http://127.0.0.1/", "http://169.254.169.254/"]:
        r = await execute_tool("fetch_page", {"url": url}, TEST_CTX)
        assert not r.success
        assert "blocked" in r.error.lower()


# ============ Unknown tool ============

@pytest.mark.asyncio
async def test_unknown_tool():
    """Unknown tool returns error"""
    r = await execute_tool("nonexistent_tool", {}, TEST_CTX)
    assert not r.success
    assert "unknown" in r.error.lower()
