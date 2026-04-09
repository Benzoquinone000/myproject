"""Finance Agent Tools - 金融工具组装逻辑

复用 common 工具体系，提供金融场景的工具获取和动态组装能力。
"""

import json
import re
from typing import Any

from langchain_core.tools import StructuredTool

from src.agents.common import get_buildin_tools
from src.agents.common.mcp import get_mcp_tools
from src.agents.common.tools import get_kb_based_tools, get_tavily_search, make_knowledge_graph_tool
from src.utils import logger

_INVALID_UNICODE_ESCAPE_RE = re.compile(r"\\u(?![0-9a-fA-F]{4})")
_MAX_TOOL_OUTPUT_CHARS = 12000
_MAX_LINE_CHART_POINTS = 300


def _sanitize_news_tool_input(value: Any) -> Any:
    """清洗 get_news_data 入参中的非法转义，避免 MCP 内部正则报错。"""
    if isinstance(value, str):
        return _INVALID_UNICODE_ESCAPE_RE.sub("u", value)
    if isinstance(value, dict):
        return {k: _sanitize_news_tool_input(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_news_tool_input(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_news_tool_input(v) for v in value)
    return value


def _sanitize_news_tool_input_hard(value: Any) -> Any:
    """二次清洗：在轻度清洗失败时，移除所有反斜杠。"""
    if isinstance(value, str):
        return value.replace("\\", "")
    if isinstance(value, dict):
        return {k: _sanitize_news_tool_input_hard(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_news_tool_input_hard(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_news_tool_input_hard(v) for v in value)
    return value


def _truncate_tool_output(result: Any, max_chars: int = _MAX_TOOL_OUTPUT_CHARS) -> Any:
    """限制工具输出体积，避免下轮模型输入 token 爆炸。"""
    try:
        if isinstance(result, str):
            if len(result) <= max_chars:
                return result
            return result[:max_chars] + "\n\n[输出过长，已截断]"

        if isinstance(result, (dict, list, tuple)):
            text = json.dumps(result, ensure_ascii=False, default=str)
            if len(text) <= max_chars:
                return result
            return text[:max_chars] + "\n\n[输出过长，已截断]"

        text = str(result)
        if len(text) <= max_chars:
            return result
        return text[:max_chars] + "\n\n[输出过长，已截断]"
    except Exception:
        text = str(result)
        if len(text) <= max_chars:
            return result
        return text[:max_chars] + "\n\n[输出过长，已截断]"


def _downsample_list(items: list[Any], max_points: int = _MAX_LINE_CHART_POINTS) -> list[Any]:
    """对超长列表做等间隔降采样，并保留首尾点。"""
    n = len(items)
    if n <= max_points:
        return items
    if max_points <= 2:
        return [items[0], items[-1]]
    step = (n - 1) / (max_points - 1)
    sampled = []
    for i in range(max_points):
        idx = round(i * step)
        sampled.append(items[idx])
    return sampled


def _compress_line_chart_input(value: Any) -> Any:
    """压缩 generate_line_chart 的输入，避免数据点过多导致上下文爆炸。"""
    if isinstance(value, dict):
        compressed = {}
        for k, v in value.items():
            key = str(k).lower()
            if (
                isinstance(v, list)
                and len(v) > _MAX_LINE_CHART_POINTS
                and key
                in {
                    "x",
                    "y",
                    "data",
                    "values",
                    "labels",
                    "points",
                    "series",
                    "datasets",
                }
            ):
                compressed[k] = _downsample_list(v, _MAX_LINE_CHART_POINTS)
            else:
                compressed[k] = _compress_line_chart_input(v)
        return compressed
    if isinstance(value, list):
        # 列表元素为点对象时也做降采样
        if len(value) > _MAX_LINE_CHART_POINTS:
            first = value[0]
            if isinstance(first, (dict, list, tuple, int, float, str)):
                value = _downsample_list(value, _MAX_LINE_CHART_POINTS)
        return [_compress_line_chart_input(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_compress_line_chart_input(v) for v in value)
    return value


def _patch_news_tool(tool: Any) -> Any:
    """为 get_news_data 创建安全包装工具（不修改原对象字段）。"""
    tool_name = str(getattr(tool, "name", "") or "")
    if "get_news_data" not in tool_name:
        return tool
    logger.info(f"Applying safety patch for MCP tool: {tool_name}")

    async def _safe_coroutine(**kwargs):
        sanitized = _sanitize_news_tool_input(kwargs)
        try:
            result = await tool.ainvoke(sanitized)
            return _truncate_tool_output(result)
        except Exception as e:
            if "Invalid regular expression" in str(e):
                logger.warning("Retry get_news_data with hard-sanitized input")
                hard_sanitized = _sanitize_news_tool_input_hard(kwargs)
                try:
                    result = await tool.ainvoke(hard_sanitized)
                    return _truncate_tool_output(result)
                except Exception as e2:
                    # 降级为可读文本，避免整个对话流中断
                    return f"新闻工具调用失败（已自动清洗参数后重试仍失败）: {e2}"
            raise

    def _safe_func(**kwargs):
        sanitized = _sanitize_news_tool_input(kwargs)
        try:
            result = tool.invoke(sanitized)
            return _truncate_tool_output(result)
        except Exception as e:
            if "Invalid regular expression" in str(e):
                logger.warning("Retry get_news_data (sync) with hard-sanitized input")
                hard_sanitized = _sanitize_news_tool_input_hard(kwargs)
                try:
                    result = tool.invoke(hard_sanitized)
                    return _truncate_tool_output(result)
                except Exception as e2:
                    return f"新闻工具调用失败（已自动清洗参数后重试仍失败）: {e2}"
            raise

    # 返回新的 StructuredTool，避免给 Pydantic 对象动态加字段导致报错
    return StructuredTool.from_function(
        func=_safe_func,
        coroutine=_safe_coroutine,
        name=tool.name,
        description=getattr(tool, "description", ""),
        args_schema=getattr(tool, "args_schema", None),
        return_direct=getattr(tool, "return_direct", False),
        metadata=getattr(tool, "metadata", None),
    )


def _patch_generic_mcp_tool(tool: Any) -> Any:
    """为任意 MCP 工具添加输出限长保护，避免上下文 token 爆炸。"""
    tool_name = str(getattr(tool, "name", "") or "")

    async def _safe_coroutine(**kwargs):
        input_data = kwargs
        if "generate_line_chart" in tool_name:
            input_data = _compress_line_chart_input(kwargs)
            if input_data != kwargs:
                logger.info(f"Compressed input points for tool: {tool_name}")
        result = await tool.ainvoke(input_data)
        return _truncate_tool_output(result)

    def _safe_func(**kwargs):
        input_data = kwargs
        if "generate_line_chart" in tool_name:
            input_data = _compress_line_chart_input(kwargs)
            if input_data != kwargs:
                logger.info(f"Compressed input points for tool: {tool_name} (sync)")
        result = tool.invoke(input_data)
        return _truncate_tool_output(result)

    return StructuredTool.from_function(
        func=_safe_func,
        coroutine=_safe_coroutine,
        name=tool.name,
        description=getattr(tool, "description", ""),
        args_schema=getattr(tool, "args_schema", None),
        return_direct=getattr(tool, "return_direct", False),
        metadata=(getattr(tool, "metadata", None) or {}) | {"finance_output_guard": True, "tool_name": tool_name},
    )


def _patch_mcp_tools(mcp_tools: list[Any]) -> list[Any]:
    """对 MCP 工具做金融场景补丁。"""
    patched_tools: list[Any] = []
    for tool in mcp_tools:
        tool_name = str(getattr(tool, "name", "") or "")
        # 先做通用限长保护
        wrapped = _patch_generic_mcp_tool(tool)
        # 新闻工具额外做参数清洗 + 失败兜底
        if "get_news_data" in tool_name:
            wrapped = _patch_news_tool(wrapped)
        patched_tools.append(wrapped)
    return patched_tools


def get_tools() -> list[Any]:
    """获取金融智能体可用的基础工具列表（供 context.py options 和主智能体使用）"""
    return get_buildin_tools()


async def get_orchestrator_tools(
    tools: list[str] | None = None,
    mcps: list[str] | None = None,
    knowledges: list[str] | None = None,
) -> list[Any]:
    """根据 context 配置动态组装主智能体的完整工具集。

    逻辑同 ChatbotAgent.get_tools()，支持：
    1. 从 context.tools 中筛选内置工具
    2. 根据 context.knowledges 加载知识库工具
    3. 根据 context.mcps 加载 MCP 工具
    """
    all_basic_tools = get_tools()
    selected_tools = []

    # 如果配置了知识库，将"查询知识图谱"工具替换为绑定范围版本
    if knowledges:
        try:
            bound_tool = make_knowledge_graph_tool(db_names=knowledges)
            all_basic_tools = [
                (bound_tool if getattr(t, "name", None) == "查询知识图谱" else t) for t in all_basic_tools
            ]
        except Exception as e:
            logger.warning(f"Failed to bind knowledge graph query tool: {e}")

    # 1. 基础工具筛选
    if tools:
        tools_map = {t.name: t for t in all_basic_tools}
        for tool_name in tools:
            if tool_name in tools_map:
                selected_tools.append(tools_map[tool_name])

    # 2. 知识库工具
    if knowledges:
        kb_tools = get_kb_based_tools(db_names=knowledges)
        selected_tools.extend(kb_tools)

    # 3. MCP 工具
    if mcps:
        for server_name in mcps:
            mcp_tools = await get_mcp_tools(server_name)
            selected_tools.extend(_patch_mcp_tools(mcp_tools))

    return selected_tools


async def get_data_agent_tools(mcps: list[str] | None = None, knowledges: list[str] | None = None) -> list[Any]:
    """数据获取子智能体的工具集：股票行情 MCP + 搜索 + 知识库"""
    tools = []

    # Tavily 搜索
    tavily = get_tavily_search()
    if tavily:
        tools.append(tavily)

    # 股票行情 MCP
    if mcps:
        for name in mcps:
            if name in ("china_stock_mcp", "time"):
                mcp_tools = await get_mcp_tools(name)
                tools.extend(_patch_mcp_tools(mcp_tools))

    # 知识库工具
    if knowledges:
        kb_tools = get_kb_based_tools(db_names=knowledges)
        tools.extend(kb_tools)

    return tools


async def get_analysis_agent_tools(knowledges: list[str] | None = None) -> list[Any]:
    """分析推理子智能体的工具集：计算器 + 知识图谱 + 知识库"""
    from src.agents.common.tools import calculator, query_knowledge_graph

    tools = [calculator]

    # 知识图谱（如有知识库则绑定范围）
    if knowledges:
        try:
            tools.append(make_knowledge_graph_tool(db_names=knowledges))
        except Exception:
            tools.append(query_knowledge_graph)
        # 知识库检索工具
        kb_tools = get_kb_based_tools(db_names=knowledges)
        tools.extend(kb_tools)
    else:
        tools.append(query_knowledge_graph)

    return tools


async def get_viz_agent_tools(mcps: list[str] | None = None) -> list[Any]:
    """可视化子智能体的工具集：图表 MCP"""
    tools = []

    if mcps:
        for name in mcps:
            if name == "mcp_server_chart":
                mcp_tools = await get_mcp_tools(name)
                tools.extend(mcp_tools)

    if not tools:
        logger.warning("finance-viz-agent: 未配置 mcp_server_chart，可视化能力受限")

    return tools
