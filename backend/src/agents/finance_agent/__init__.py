"""Finance Agent - 金融数据分析与决策多智能体模块

融合 ChatbotAgent 的 tools/MCP/知识库动态选择能力和 DeepAgent 的多智能体协作架构，
构建具备数据获取、分析推理、图表可视化和报告生成能力的金融分析智能体。
"""

from .context import FinanceContext
from .graph import FinanceAgent

__all__ = [
    "FinanceAgent",
    "FinanceContext",
]

__version__ = "1.0.0"
__description__ = "金融数据分析与决策多智能体系统"
