from dataclasses import dataclass, field
from typing import Annotated

from src.agents.common import BaseContext, gen_tool_info
from src.agents.common.mcp import MCP_DISPLAY_LABELS, MCP_SERVERS
from src.knowledge import knowledge_base

from .tools import get_tools


@dataclass(kw_only=True)
class Context(BaseContext):
    tools: Annotated[list[dict], {"__template_metadata__": {"kind": "tools"}}] = field(
        default_factory=list,
        metadata={
            "name": "工具",
            "options": lambda: gen_tool_info(get_tools()),  # 这里的选择是所有的工具
            "description": "内置的部分工具，包含 common 工具和本智能体的特有工具（不含 MCP）。",
        },
    )

    knowledges: list[str] = field(
        default_factory=list,
        metadata={
            "name": "知识库",
            "options": lambda: [k["name"] for k in knowledge_base.get_retrievers().values()],
            "description": "知识库列表，可以在左侧知识库页面中创建知识库。",
            "type": "list",  # Explicitly mark as list type for frontend if needed
        },
    )

    mcps: list[str] = field(
        default_factory=list,
        metadata={
            "name": "MCP服务器",
            "type": "list",
            "options": lambda: list(MCP_SERVERS.keys()),
            "option_labels": lambda: {k: MCP_DISPLAY_LABELS.get(k, k) for k in MCP_SERVERS.keys()},
            "description": (
                "MCP 服务器列表，选项来自后端 `MCP_SERVERS`；"
                "stdio 类（如 npx）会在本机或容器内按需启动子进程。"
            ),
        },
    )
