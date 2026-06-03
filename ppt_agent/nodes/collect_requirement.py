import json

from langchain_core.messages import HumanMessage, SystemMessage

from ppt_agent.services.LLm import llm

from ppt_agent.state import State


def collect_r_node(state: State) -> dict:
    """从用户消息中提取 PPT 需求信息。"""
    messages = state.get("messages", [])

    if not messages:
        return {
            "requirement": {},
            "status": "failed",
            "error": "没有找到用户消息。",
        }

    user_message = messages[-1].content

    res = llm.invoke(
        [
            SystemMessage(
                content="""
你是一个 PPT 需求信息提取工具。

你需要从用户的需求中提取关键信息，并且只返回 JSON，不要返回任何解释文字。

JSON 格式如下：

{
  "topic": "PPT 题目",
  "use_case": "使用场景",
  "audience": "目标受众",
  "page_count": 20,
  "style": "视觉风格",
  "language": "zh-CN",
  "key_points": ["重点1", "重点2"],
  "source_files": []
}

如果某个字段没有提到：
- 字符串字段用空字符串 ""
- page_count 用 null
- key_points 用 []
- source_files 用 []
"""
            ),
            HumanMessage(content=user_message),
        ]
    )

    extracted_requirement = json.loads(res.content)

    old_requirement = state.get("requirement", {})
    requirement = {
        **old_requirement,
        **{
            key: value
            for key, value in extracted_requirement.items()
            if value not in ("", None, [])
        },
    }

    return {
        "requirement": requirement,
        "status": "collecting",
    }
