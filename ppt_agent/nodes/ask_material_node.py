from ppt_agent.state import State


def ask_m_node(state: State) -> dict:
    """需求完整后，询问用户是否添加资料。"""
    return {
        "assistant_reply": (
            "需求信息已经完整。是否要添加资料？\n\n"
            "请直接回复：\n"
            "- 添加资料\n"
            "- 不添加，直接生成"
        ),
        "status": "waiting_material",
    }
