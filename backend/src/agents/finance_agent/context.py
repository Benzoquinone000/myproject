"""Finance Agent Context - 融合 Chatbot + Deep 的上下文配置"""

from dataclasses import dataclass, field
from typing import Annotated

from src.agents.common.context import BaseContext
from src.agents.common.mcp import MCP_DISPLAY_LABELS, MCP_SERVERS
from src.knowledge import knowledge_base

from .prompts import FINANCE_ORCHESTRATOR_PROMPT
from .tools import get_tools


@dataclass(kw_only=True)
class FinanceContext(BaseContext):
    """
    金融智能体的上下文配置，融合 ChatbotAgent 的动态工具选择和 DeepAgent 的子智能体模型配置。

    配置优先级: 运行时配置 > config.yaml > 类默认值
    """

    # 系统提示词（默认使用金融编排 prompt，可被 config.yaml 覆盖）
    system_prompt: Annotated[str, {"__template_metadata__": {"kind": "prompt"}}] = field(
        default=FINANCE_ORCHESTRATOR_PROMPT,
        metadata={"name": "系统提示词", "description": "金融智能体的角色和行为指导"},
    )

    # 子智能体模型（同 DeepAgent）
    subagents_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="siliconflow/Pro/deepseek-ai/DeepSeek-V3.2",
        metadata={
            "name": "子智能体模型",
            "description": "子智能体（数据获取、分析、可视化、评审）使用的模型。",
        },
    )

    # 动态工具选择（同 ChatbotAgent）
    tools: Annotated[list[dict], {"__template_metadata__": {"kind": "tools"}}] = field(
        default_factory=list,
        metadata={
            "name": "工具",
            "options": lambda: _gen_tool_info(),
            "description": "内置工具列表（不含 MCP）。主智能体可直接使用这些工具完成轻量查询。",
        },
    )

    # MCP 服务器选择（同 ChatbotAgent，默认包含金融相关 MCP）
    mcps: list[str] = field(
        default_factory=list,
        metadata={
            "name": "MCP服务器",
            "type": "list",
            "options": lambda: list(MCP_SERVERS.keys()),
            "option_labels": lambda: {k: MCP_DISPLAY_LABELS.get(k, k) for k in MCP_SERVERS.keys()},
            "description": (
                "MCP 服务器列表。金融场景建议启用 china-stock-mcp（股票行情）与 "
                "mcp_server_chart（图表生成）；需要当前时间时可启用 time，并配合搜索与知识库。"
            ),
        },
    )

    # 知识库选择（同 ChatbotAgent）
    knowledges: list[str] = field(
        default_factory=list,
        metadata={
            "name": "知识库",
            "options": lambda: [k["name"] for k in knowledge_base.get_retrievers().values()],
            "description": "知识库列表，可用于检索历史数据、研报、行业资料等。",
            "type": "list",
        },
    )


def _gen_tool_info():
    """延迟生成工具信息，避免循环导入"""
    from src.agents.common import gen_tool_info

    return gen_tool_info(get_tools())
