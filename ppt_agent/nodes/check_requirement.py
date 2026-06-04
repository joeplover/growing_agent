from ppt_agent.state import State


GENERIC_VALUES = {
    "topic": {
        "ppt",
        "制作ppt",
        "做ppt",
        "一个ppt",
        "ppt制作",
        "演示文稿",
        "presentation",
    },
    "use_case": {
        "制作ppt",
        "做ppt",
        "ppt制作",
        "展示",
        "演示",
        "汇报",
        "未指定",
        "默认",
    },
    "audience": {
        "用户",
        "用户自己",
        "自己",
        "本人",
        "未指定",
        "默认",
    },
    "style": {
        "默认",
        "默认风格",
        "简洁",
        "普通",
        "未指定",
    },
}


def check_r_node(state:State):
    """
    检查需求是否足够创建 PPT Brief

    最小必填字段：
    topic
    use_case
    audience
    page_count
    style

    输出：
    state["requirement_complete"] = True 或 False
    state["missing_fields"] = ["audience", "page_count"]
    """

    required_fields = [
        "topic",
        "use_case",
        "audience",
        "page_count",
        "style",
    ]
    requirement = state.get("requirement",{})

    missing_fields = []

    for field in required_fields:
        value = requirement.get(field)
        if not value or _is_generic_value(field, value):
            missing_fields.append(field)

    if len(missing_fields) == len(required_fields):
        return {
            "requirement_complete": False,
            "missing_fields": required_fields,
        }

    return {
        "requirement_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }


def _is_generic_value(field: str, value) -> bool:
    normalized = str(value).strip().lower().replace(" ", "")

    if field == "page_count":
        return False

    return normalized in GENERIC_VALUES.get(field, set())
