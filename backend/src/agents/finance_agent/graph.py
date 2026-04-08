"""Finance Agent - 金融数据分析与决策多智能体

融合 ChatbotAgent 的动态工具加载和 DeepAgent 的多智能体协作架构。
"""

import json

from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,
    TodoListMiddleware,
    ToolCallLimitMiddleware,
)

from src.agents.common import BaseAgent, load_chat_model
from src.agents.common.middlewares import inject_attachment_context
from src.utils import logger

from .context import FinanceContext
from .prompts import (
    FINANCE_ANALYSIS_PROMPT,
    FINANCE_CRITIQUE_PROMPT,
    FINANCE_DATA_PROMPT,
    FINANCE_VIZ_PROMPT,
)
from .tools import (
    get_analysis_agent_tools,
    get_data_agent_tools,
    get_orchestrator_tools,
    get_viz_agent_tools,
)


class FinanceAgent(BaseAgent):
    name = "金融数据分析智能体"
    description = "具备数据获取、分析推理、图表可视化和报告生成能力的金融多智能体系统"
    context_schema = FinanceContext
    capabilities = [
        "file_upload",
        "todo",
        "files",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.graph = None
        self.checkpointer = None

    async def get_graph(self, input_context=None, **kwargs):
        """构建金融多智能体协作图。

        融合两种模式：
        - ChatbotAgent 模式：根据 context 动态加载 tools/MCP/知识库（支持配置变更后重建）
        - DeepAgent 模式：SubAgentMiddleware 实现 4 个子智能体协作
        """
        # 获取上下文配置
        context = self.context_schema.from_file(module_name=self.module_name, input_context=input_context)

        # 缓存键：配置变更时重建 graph（同 ChatbotAgent）
        cache_payload = {
            "model": context.model,
            "subagents_model": context.subagents_model,
            "system_prompt": context.system_prompt,
            "tools": context.tools,
            "mcps": context.mcps,
            "knowledges": context.knowledges,
        }
        cache_key = json.dumps(cache_payload, ensure_ascii=False, sort_keys=True, default=str)

        if self.graph and getattr(self, "_graph_cache_key", None) == cache_key:
            return self.graph

        # 加载模型
        model = load_chat_model(context.model)
        sub_model = load_chat_model(context.subagents_model)

        # 动态加载主智能体工具
        orchestrator_tools = await get_orchestrator_tools(
            tools=context.tools,
            mcps=context.mcps,
            knowledges=context.knowledges,
        )

        # 加载各子智能体的工具集
        data_tools = await get_data_agent_tools(mcps=context.mcps, knowledges=context.knowledges)
        analysis_tools = await get_analysis_agent_tools(knowledges=context.knowledges)
        viz_tools = await get_viz_agent_tools(mcps=context.mcps)

        # 构建子智能体配置
        subagents = self._build_subagents(data_tools, analysis_tools, viz_tools)

        # 子智能体默认中间件
        default_sub_middleware = [
            TodoListMiddleware(),
            FilesystemMiddleware(),
            SummarizationMiddleware(
                model=sub_model,
                trigger=("tokens", 40000),
                keep=("messages", 4),
                trim_tokens_to_summarize=None,
            ),
            PatchToolCallsMiddleware(),
            # tavily_search 单次运行最多 3 次
            ToolCallLimitMiddleware(
                tool_name="tavily_search",
                run_limit=5,
                exit_behavior="continue",
            ),
            # 每个子智能体单次运行最多 14 轮工具调用
            ToolCallLimitMiddleware(
                run_limit=14,
                exit_behavior="end",
            ),
        ]

        # 构建主智能体图
        graph = create_agent(
            model=model,
            tools=orchestrator_tools,
            system_prompt=context.system_prompt,
            middleware=[
                inject_attachment_context,
                TodoListMiddleware(),
                FilesystemMiddleware(),
                SubAgentMiddleware(
                    default_model=sub_model,
                    default_tools=data_tools,  # 默认工具集给通用子智能体
                    subagents=subagents,
                    default_middleware=default_sub_middleware,
                    general_purpose_agent=True,
                ),
                SummarizationMiddleware(
                    model=model,
                    trigger=("tokens", 60000),
                    keep=("messages", 6),
                    trim_tokens_to_summarize=None,
                ),
                PatchToolCallsMiddleware(),
                # Tavily 搜索总调用限制
                ToolCallLimitMiddleware(
                    tool_name="tavily_search",
                    thread_limit=16,
                    exit_behavior="continue",
                ),
                # 总工具调用轮次限制
                ToolCallLimitMiddleware(
                    run_limit=50,
                    exit_behavior="end",
                ),
            ],
            checkpointer=await self._get_checkpointer(),
        )

        self.graph = graph
        self._graph_cache_key = cache_key
        logger.info(
            f"FinanceAgent graph built: {len(orchestrator_tools)} orchestrator tools, "
            f"{len(data_tools)} data tools, {len(analysis_tools)} analysis tools, "
            f"{len(viz_tools)} viz tools"
        )
        return graph

    @staticmethod
    def _build_subagents(data_tools: list, analysis_tools: list, viz_tools: list) -> list[dict]:
        """构建 4 个金融子智能体配置"""
        return [
            {
                "name": "finance-data-agent",
                "description": (
                    "金融数据获取员。负责使用股票行情工具、网页搜索和知识库获取行情、基本面、新闻等数据。"
                    "将数据要点写入 finance_workspace/data_notes.md。"
                ),
                "system_prompt": FINANCE_DATA_PROMPT,
                "tools": data_tools,
            },
            {
                "name": "finance-analysis-agent",
                "description": (
                    "金融分析师。基于已获取的数据进行指标解读、对比分析和情景讨论。"
                    "使用计算器和知识图谱辅助分析，将分析要点写入 finance_workspace/analysis_notes.md。"
                ),
                "system_prompt": FINANCE_ANALYSIS_PROMPT,
                "tools": analysis_tools,
            },
            {
                "name": "finance-viz-agent",
                "description": (
                    "金融数据可视化专员。根据数据和分析结果使用 AntV 图表 MCP 生成专业图表。"
                    "返回图表 URL/路径供报告引用。"
                ),
                "system_prompt": FINANCE_VIZ_PROMPT,
                "tools": viz_tools,
            },
            {
                "name": "finance-critique-agent",
                "description": (
                    "金融报告评审员。审阅 final_report.md，从数据准确性、分析深度、"
                    "合规性、结构完整性等维度提供改进建议。"
                ),
                "system_prompt": FINANCE_CRITIQUE_PROMPT,
                "tools": [],  # 评审员只需读取文件系统，无需额外工具
            },
        ]
