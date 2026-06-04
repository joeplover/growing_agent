from ppt_agent.state import State

FIELD_QUESTIONS = {
    "topic": ("题目", "PPT 的具体题目是什么？"),
    "use_case": ("场景", "这份 PPT 用在什么场景？比如毕业答辩、项目汇报、商业路演。"),
    "audience": ("受众", "这份 PPT 是给谁看的？比如答辩老师、领导、客户。"),
    "page_count": ("页数", "你希望大概做多少页？"),
    "style": ("风格", "你希望 PPT 是什么风格？比如科技蓝、商务简洁、学术答辩风。"),
}


def ask_f_node(state:State):
    """需求不完整时，向用户追问。"""
    missing_fields = state.get("missing_fields", [])
    field_items = [
        FIELD_QUESTIONS[field] for field in missing_fields if field in FIELD_QUESTIONS
    ]
    if not field_items:
        field_items = list(FIELD_QUESTIONS.values())

    field_names = "、".join(label for label, _ in field_items)
    assistant_reply = "\n".join(
        [
            f"我需要你补充这些信息：{field_names}。",
            "",
            *[
                f"- **{label}**：{question}"
                for label, question in field_items
            ],
            "",
            "你可以直接按下面格式回复：",
            *[
                f"{label}："
                for label, _ in field_items
            ],
        ]
    )
    return {
        "assistant_reply": assistant_reply,
        "status": "waiting_user",
    }
