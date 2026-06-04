import json
import re

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

    user_message = _clean_followup_reply(messages[-1].content)

    if not user_message:
        return {
            "status": "collecting",
        }

    direct_requirement = _extract_direct_followup_requirement(state, user_message)
    if direct_requirement:
        old_requirement = state.get("requirement", {})
        return {
            "requirement": {**old_requirement, **direct_requirement},
            "status": "collecting",
        }

    try:
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

不要根据常识补默认值。用户只说“我要制作一个 PPT”“帮我做 PPT”时：
- topic 必须返回 ""
- use_case 必须返回 ""
- audience 必须返回 ""
- page_count 必须返回 null
- style 必须返回 ""
"""
                ),
                HumanMessage(content=user_message),
            ]
        )

        extracted_requirement = json.loads(_clean_json(res.content))
    except Exception as exc:
        return {
            "status": "failed",
            "error": f"需求信息解析失败：{exc}",
        }

    if not isinstance(extracted_requirement, dict):
        return {
            "status": "failed",
            "error": "需求信息解析失败：LLM 没有返回 JSON 对象。",
        }

    extracted_requirement = _normalize_requirement(extracted_requirement)

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


def _normalize_requirement(requirement: dict) -> dict:
    page_count = requirement.get("page_count")

    if isinstance(page_count, str):
        match = re.search(r"\d+", page_count)
        requirement["page_count"] = int(match.group()) if match else None

    return requirement


def _extract_direct_followup_requirement(state: State, user_message: str) -> dict:
    missing_fields = state.get("missing_fields") or []
    if len(missing_fields) != 1:
        return {}

    field = missing_fields[0]
    if field == "audience" and _looks_like_short_followup_value(user_message):
        return {"audience": user_message}

    if field == "page_count":
        match = re.search(r"\d+", user_message)
        if match and len(user_message) <= 12:
            return {"page_count": int(match.group())}

    if field in {"topic", "use_case", "style"} and _looks_like_short_followup_value(user_message):
        return {field: user_message}

    return {}


def _looks_like_short_followup_value(text: str) -> bool:
    value = text.strip()
    if not value:
        return False

    if "\n" in value:
        return False

    return len(value) <= 30


def _clean_followup_reply(text: str) -> str:
    value = text.strip()
    value = re.sub(r"^回复\s+[^:\n：]{1,30}[:：]\s*", "", value).strip()
    value = value.strip("\u00a0 ")
    return value


def _clean_json(text: str) -> str:
    value = text.strip()

    if value.startswith("```"):
        value = re.sub(r"^```[a-zA-Z]*", "", value).strip()
        value = re.sub(r"```$", "", value).strip()

    return value
