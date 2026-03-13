from __future__ import annotations

import asyncio

import pytest


def test_mcp_server_import() -> None:
    pytest.importorskip("mcp.server.fastmcp")
    from opendivine.mcp.server import mcp

    assert mcp is not None


def test_mcp_tool_registration() -> None:
    pytest.importorskip("mcp.server.fastmcp")
    from opendivine.mcp.server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"draw_tarot", "draw_iching", "entropy_status"}.issubset(names)
