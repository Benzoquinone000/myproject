"""MCP Client setup and management for LangGraph ReAct Agent."""

import traceback
from collections.abc import Callable
from typing import Any, cast

from langchain_core.tools import StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.utils import logger

# (工具名子串, 失败时返回给模型的提示，避免 ToolException 打断整轮对话流)
_MCP_SOFT_FAIL_BY_NAME_SUBSTR: tuple[tuple[str, str], ...] = (
    (
        "get_hist_data",
        "【历史行情数据暂不可用】公开数据源（如东方财富、新浪等）"
        "当前无法返回有效 K 线/历史数据（常见于网络限制或服务端断开）。"
        "已跳过该步骤，请改用知识库检索、新闻/搜索工具或定性分析继续完成任务，勿重复调用本工具。",
    ),
)

# pozansky-stock-server（本地 uvx 包）上工具的通用兜底：列数不匹配、无表格等
_POZANSKY_STOCK_MCP_GENERIC_SOFT_FAIL = (
    "【股票数据工具暂不可用】数据源返回异常或格式不匹配（如列数不一致、无表格数据等），"
    "已跳过本步。请改用搜索、知识库或其它工具继续完成任务，勿重复调用同一工具。"
)


def _wrap_mcp_tool_soft_fail(inner: Any, user_hint: str) -> Any:
    """将 MCP 工具包装为：异常时返回提示字符串，不向 LangGraph 抛 ToolException。"""

    tool_name = getattr(inner, "name", "mcp_tool")

    async def _coro(**kwargs: Any) -> Any:
        try:
            return await inner.ainvoke(kwargs)
        except Exception as e:
            logger.warning("MCP tool '%s' failed; returning soft-fail message: %s", tool_name, e)
            return user_hint

    def _sync(**kwargs: Any) -> Any:
        try:
            return inner.invoke(kwargs)
        except Exception as e:
            logger.warning("MCP tool '%s' failed (sync); returning soft-fail message: %s", tool_name, e)
            return user_hint

    return StructuredTool.from_function(
        func=_sync,
        coroutine=_coro,
        name=inner.name,
        description=getattr(inner, "description", ""),
        args_schema=getattr(inner, "args_schema", None),
        return_direct=getattr(inner, "return_direct", False),
        metadata=getattr(inner, "metadata", None),
    )


def _apply_mcp_soft_fail_wrappers(tools: list[Any]) -> list[Any]:
    out: list[Any] = []
    for tool in tools:
        name = str(getattr(tool, "name", "") or "")
        hint: str | None = None
        for substr, message in _MCP_SOFT_FAIL_BY_NAME_SUBSTR:
            if substr in name:
                hint = message
                break
        if hint is None:
            out.append(tool)
        else:
            out.append(_wrap_mcp_tool_soft_fail(tool, hint))
    return out


def _wrap_pozansky_stock_mcp_tools(tools: list[Any]) -> list[Any]:
    """对股票 MCP 全部工具做异常兜底，避免单次工具失败中断整轮流式对话。"""
    out: list[Any] = []
    for tool in tools:
        name = str(getattr(tool, "name", "") or "")
        hint: str | None = None
        for substr, message in _MCP_SOFT_FAIL_BY_NAME_SUBSTR:
            if substr in name:
                hint = message
                break
        if hint is None:
            hint = _POZANSKY_STOCK_MCP_GENERIC_SOFT_FAIL
        out.append(_wrap_mcp_tool_soft_fail(tool, hint))
    return out


# Global MCP tools cache
_mcp_tools_cache: dict[str, list[Callable[..., Any]]] = {}

# MCP Server configurations
MCP_SERVERS = {
    "sequentialthinking": {
        "url": "https://remote.mcpservers.org/sequentialthinking/mcp",
        "transport": "streamable_http",
    },
    # "zhipu-web-search-sse": {
    #     "url": f"https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization={os.getenv('ZHIPUAI_API_KEY')}",
    #     "transport": "streamable_http",
    # },
    # stdio：由客户端按需拉起子进程（Docker 镜像已含 uvx，首次会下载 mcp-server-time）
    "time": {
        "command": "uvx",
        "args": ["mcp-server-time"],
        "transport": "stdio",
    },
    "mcp_server_chart": {"command": "npx", "args": ["-y", "@antv/mcp-server-chart"], "transport": "stdio"},
    # 本地 stdio：uvx 拉起 pozansky-stock-server（与 Cursor command/args 一致，需本机已装 uv）
    "pozansky-stock-server": {
        "command": "uvx",
        "args": ["pozansky-stock-server"],
        "transport": "stdio",
    },
}

# 前端「MCP 服务器」多选项展示用（键与 MCP_SERVERS 一致；未列出的键默认显示为键名）
MCP_DISPLAY_LABELS: dict[str, str] = {
    "sequentialthinking": "顺序思考（远程）",
    "time": "时间（mcp-server-time / uvx）",
    "mcp_server_chart": "AntV 图表 MCP（npx）",
    "pozansky-stock-server": "股票行情（Pozansky / uvx 本地）",
}


async def get_mcp_client(
    server_configs: dict[str, Any] | None = None,
) -> MultiServerMCPClient | None:
    """Initializes an MCP client with the given server configurations."""
    try:
        client = MultiServerMCPClient(server_configs)  # pyright: ignore[reportArgumentType]
        logger.info(f"Initialized MCP client with servers: {list(server_configs.keys())}")
        return client
    except Exception as e:
        logger.error("Failed to initialize MCP client: {}", e)
        return None


async def get_mcp_tools(server_name: str, additional_servers: dict[str, dict] = None) -> list[Callable[..., Any]]:
    """Get MCP tools for a specific server, initializing client if needed."""
    global _mcp_tools_cache

    # Return cached tools if available
    if server_name in _mcp_tools_cache:
        return _mcp_tools_cache[server_name]

    mcp_servers = MCP_SERVERS | (additional_servers or {})

    try:
        assert server_name in mcp_servers, f"Server {server_name} not found in ({list(mcp_servers.keys())})"
        client = await get_mcp_client({server_name: mcp_servers[server_name]})
        if client is None:
            return []

        # Get all tools and filter by server (if tools have server metadata)
        all_tools = await client.get_tools()
        tools = cast(list[Callable[..., Any]], all_tools)
        if server_name == "pozansky-stock-server":
            tools = _wrap_pozansky_stock_mcp_tools(tools)
        else:
            tools = _apply_mcp_soft_fail_wrappers(tools)

        _mcp_tools_cache[server_name] = tools
        logger.info(f"Loaded {len(tools)} tools from MCP server '{server_name}'")
        return tools
    except AssertionError as e:
        logger.warning(f"[assert] Failed to load tools from MCP server '{server_name}': {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to load tools from MCP server '{server_name}': {e}, traceback: {traceback.format_exc()}")
        return []


async def get_all_mcp_tools() -> list[Callable[..., Any]]:
    """Get all tools from all configured MCP servers."""
    all_tools = []
    for server_name in MCP_SERVERS.keys():
        tools = await get_mcp_tools(server_name)
        all_tools.extend(tools)
    return all_tools


def add_mcp_server(name: str, config: dict[str, Any]) -> None:
    """Add a new MCP server configuration."""
    MCP_SERVERS[name] = config
    # Clear client to force reinitialization with new config
    clear_mcp_cache()


def clear_mcp_cache() -> None:
    """Clear the MCP tools cache (useful for testing)."""
    global _mcp_tools_cache
    _mcp_tools_cache = {}
