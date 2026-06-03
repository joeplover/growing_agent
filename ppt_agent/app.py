from langchain_core.messages import HumanMessage

from ppt_agent.graph import app


def main() -> None:
    state = {
        "messages": [],
        "requirement": {},
    }

    print("PPT Agent 已启动。输入 exit 退出。")

    while True:
        user_input = input("\n你：").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        state["messages"].append(HumanMessage(content=user_input))

        if state.get("status") == "waiting_confirm":
            print("\nAgent：已收到确认，开始生成 PPT，请稍等...")

        state = app.invoke(state)

        if state.get("assistant_reply"):
            print(f"\nAgent：{state['assistant_reply']}")

        if state.get("status") == "project_created":
            print(f"\nAgent：项目已创建：{state.get('project_path')}")
            break

        if state.get("status") == "ppt_exported":
            print(f"\nAgent：PPT 已生成：{state.get('pptx_path')}")
            break

        if state.get("status") == "failed":
            print(f"\nAgent：运行失败：{state.get('error')}")
            break


if __name__ == "__main__":
    main()
