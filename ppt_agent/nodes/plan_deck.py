import json

from langchain_core.messages import HumanMessage, SystemMessage

from ppt_agent.services.LLm import llm
from ppt_agent.state import State


def p_d_node(state: State) -> dict:
    """根据 PPT Brief 生成页面大纲。"""
    ppt_brief = state.get("ppt_brief", {})

    res = llm.invoke(
        [
            SystemMessage(
                content=(
                    "你是一个 PPT 大纲规划助手。"
                    "请只返回 JSON 数组，不要返回解释文字。"
                )
            ),
            HumanMessage(
                content=f"""
请根据下面的 PPT Brief 生成 PPT 页面大纲：

{ppt_brief}

输出格式必须是 JSON 数组，例如：

[
  {{
    "page": 1,
    "title": "封面",
    "purpose": "展示题目、学生、导师",
    "rhythm": "anchor"
  }},
  {{
    "page": 2,
    "title": "目录",
    "purpose": "展示汇报结构",
    "rhythm": "breathing"
  }}
]

rhythm 只能从这三个里面选：
- anchor
- breathing
- dense
"""
            ),
        ]
    )

    deck_outline = json.loads(res.content)

    return {
        "deck_outline": deck_outline,
        "status": "outline_ready",
    }