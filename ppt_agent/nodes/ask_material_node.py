from ppt_agent.state import State


def ask_m_node(state: State) -> dict:
    """需求完整后，询问用户是否引入资料文件夹。"""
    return {
        "assistant_reply": (
            "需求信息已经完整。\n\n"
            "要不要引入 `materials/` 文件夹里的资料？\n\n"
            "请直接回复：\n"
            "- 引入\n"
            "- 不引入"
        ),
        "status": "waiting_material",
    }
