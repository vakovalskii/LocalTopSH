"""Tests for Docker sandbox: creation, execution, cleanup, isolation"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from tools.sandbox import (
    get_docker_client,
    get_user_ports,
    find_free_port_range,
    get_or_create_container,
    execute_in_sandbox,
    stop_user_container,
    check_workspace_size,
    get_sandbox_stats,
    cleanup_inactive_containers,
    user_containers,
    CONTAINER_PREFIX,
    SANDBOX_IMAGE,
)


# ============ Docker client ============

def test_docker_client_available():
    """Docker client should connect"""
    client = get_docker_client()
    assert client is not None
    assert client.ping()


# ============ Port allocation ============

def test_port_allocation_deterministic():
    """Same user_id always gets same ports"""
    base1, ports1 = get_user_ports("123456")
    base2, ports2 = get_user_ports("123456")
    assert base1 == base2
    assert ports1 == ports2


def test_port_allocation_range():
    """Ports should be in 5000-5999"""
    for uid in ["100", "999", "123456789", "1"]:
        base, ports = get_user_ports(uid)
        assert 5000 <= base < 6000, f"Base {base} out of range for user {uid}"
        assert len(ports) == 10
        assert ports[-1] < 6000


def test_port_allocation_different_users():
    """Different users should get different ports (usually)"""
    ports_set = set()
    collisions = 0
    for i in range(50):
        base, _ = get_user_ports(str(1000000 + i))
        if base in ports_set:
            collisions += 1
        ports_set.add(base)
    # Some collisions possible (hash), but not too many
    assert collisions < 25, f"Too many port collisions: {collisions}/50"


def test_find_free_port_range():
    """Should find a free range"""
    result = find_free_port_range()
    assert result is not None
    base, ports = result
    assert 5000 <= base < 6000
    assert len(ports) == 10


# ============ Container lifecycle ============

TEST_USER = "test_99999"


@pytest.mark.asyncio
async def test_container_create():
    """Create sandbox container for user"""
    # Cleanup any existing
    await stop_user_container(TEST_USER)
    
    container = await get_or_create_container(TEST_USER)
    assert container is not None
    assert container.user_id == TEST_USER
    assert len(container.ports) == 10
    assert container.container_id
    
    # Verify in Docker
    client = get_docker_client()
    docker_container = client.containers.get(container.container_id)
    assert docker_container.status == "running"
    
    # Cleanup
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_container_reuse():
    """Second call reuses existing container"""
    await stop_user_container(TEST_USER)
    
    c1 = await get_or_create_container(TEST_USER)
    c2 = await get_or_create_container(TEST_USER)
    
    assert c1.container_id == c2.container_id
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_execute_in_sandbox():
    """Execute command in sandbox"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "echo hello sandbox")
    assert sandboxed, "Should run in sandbox"
    assert success, f"Command failed: {output}"
    assert "hello sandbox" in output
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_execute_python_in_sandbox():
    """Python available in sandbox"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "python3 -c 'print(2+2)'")
    assert sandboxed
    assert success, f"Python failed: {output}"
    assert "4" in output
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_execute_failing_command():
    """Failed command returns error"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "ls /nonexistent_xyz")
    assert sandboxed
    assert not success
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_sandbox_isolation_no_secrets():
    """Sandbox should NOT have access to Docker secrets"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "ls /run/secrets/ 2>&1 || echo 'no secrets dir'")
    assert sandboxed
    # Either fails or shows no secrets
    assert "api_key" not in output.lower()
    assert "telegram" not in output.lower()
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_sandbox_isolation_no_env():
    """Sandbox should NOT have sensitive env vars"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "env")
    assert sandboxed
    assert "API_KEY" not in output
    assert "TELEGRAM" not in output
    assert "PROXY_URL" not in output
    # Only allowed env vars
    assert "USER_ID" in output
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_sandbox_workspace_isolation():
    """Sandbox should only see own workspace"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "ls /workspace/ 2>&1")
    assert sandboxed
    # Should only have user's own directory or nothing
    assert "_shared" not in output
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_sandbox_df_intercept():
    """df command should show workspace usage"""
    await stop_user_container(TEST_USER)
    
    success, output, sandboxed = await execute_in_sandbox(TEST_USER, "df")
    assert sandboxed
    assert "Workspace" in output or "workspace" in output.lower()
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_stop_container():
    """stop_user_container removes container"""
    container = await get_or_create_container(TEST_USER)
    assert container is not None
    
    container_id = container.container_id
    await stop_user_container(TEST_USER)
    
    assert TEST_USER not in user_containers
    
    # Verify removed from Docker
    client = get_docker_client()
    with pytest.raises(Exception):
        client.containers.get(container_id)


@pytest.mark.asyncio
async def test_sandbox_stats():
    """get_sandbox_stats returns info"""
    await stop_user_container(TEST_USER)
    
    stats = get_sandbox_stats()
    assert "active_containers" in stats
    assert isinstance(stats["containers"], list)


@pytest.mark.asyncio
async def test_sandbox_resource_limits():
    """Container should have resource limits"""
    await stop_user_container(TEST_USER)
    
    container = await get_or_create_container(TEST_USER)
    assert container is not None
    
    client = get_docker_client()
    docker_container = client.containers.get(container.container_id)
    attrs = docker_container.attrs
    
    # Check memory limit (512MB = 536870912)
    mem_limit = attrs.get("HostConfig", {}).get("Memory", 0)
    assert mem_limit == 536870912, f"Memory limit {mem_limit} != 512MB"
    
    # Check PID limit
    pids = attrs.get("HostConfig", {}).get("PidsLimit", 0)
    assert pids == 100, f"PID limit {pids} != 100"
    
    # Check CPU quota (50%)
    cpu_quota = attrs.get("HostConfig", {}).get("CpuQuota", 0)
    assert cpu_quota == 50000, f"CPU quota {cpu_quota} != 50000"
    
    await stop_user_container(TEST_USER)


@pytest.mark.asyncio
async def test_sandbox_security_opts():
    """Container should have security options"""
    await stop_user_container(TEST_USER)
    
    container = await get_or_create_container(TEST_USER)
    assert container is not None
    
    client = get_docker_client()
    docker_container = client.containers.get(container.container_id)
    sec_opts = docker_container.attrs.get("HostConfig", {}).get("SecurityOpt", [])
    
    assert "no-new-privileges" in sec_opts, f"Missing no-new-privileges: {sec_opts}"
    
    await stop_user_container(TEST_USER)
