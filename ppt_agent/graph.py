from langgraph.constants import END
from langgraph.graph import StateGraph

from ppt_agent.nodes.ask_followup import a_f_node
from ppt_agent.nodes.check_requirement import c_r_node
from ppt_agent.nodes.collect_requirement import collect_r_node
from ppt_agent.nodes.create_project import c_p_node
from ppt_agent.nodes.freeze_brief import f_b_node
from ppt_agent.nodes.plan_deck import p_d_node
from ppt_agent.state import State


def route(state: State) -> str:
    status = state.get("requirement_complete")
    if status == True:
        return "freeze_brief_node"
    else:
        return "ask_followup_node"

wf = StateGraph(State)
wf.add_node("check_requirement_node",c_r_node)
wf.add_node("ask_followup_node",a_f_node)
wf.add_node("collect_requirement_node",collect_r_node)
wf.add_node("create_project_node",c_p_node)
wf.add_node("freeze_brief_node",f_b_node)
wf.add_node("plan_deck_node",p_d_node)
wf.set_entry_point("collect_requirement_node")
wf.add_edge("collect_requirement_node","check_requirement_node")
wf.add_conditional_edges(
    "check_requirement_node",
    route
)
wf.add_edge("ask_followup_node",END)
wf.add_edge("freeze_brief_node","plan_deck_node")
wf.add_edge("plan_deck_node","create_project_node")
wf.add_edge("create_project_node",END)

app = wf.compile()

