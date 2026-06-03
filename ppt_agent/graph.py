from langgraph.constants import END, START
from langgraph.graph import StateGraph

from ppt_agent.nodes.ask_followup import ask_f_node
from ppt_agent.nodes.ask_material_node import ask_m_node
from ppt_agent.nodes.check_requirement import check_r_node
from ppt_agent.nodes.check_user_confirm_node import check_u_c_node
from ppt_agent.nodes.collect_material_node import collect_m_node
from ppt_agent.nodes.collect_requirement import collect_r_node
from ppt_agent.nodes.confirm_plan_node import confirm_p_node
from ppt_agent.nodes.create_project import create_p_node
from ppt_agent.nodes.export_ppt_node import export_p_node
from ppt_agent.nodes.freeze_brief import freeze_b_node
from ppt_agent.nodes.generate_design_spec_node import generate_d_s_node
from ppt_agent.nodes.generate_spec_lock_node import generate_s_l_node
from ppt_agent.nodes.generate_svg_node import generate_s_v_g_node
from ppt_agent.nodes.plan_deck import plan_d_node
from ppt_agent.nodes.write_project_meterials_node import w_p_m_node
from ppt_agent.state import State


def route(state: State) -> str:
    if state.get("requirement_complete") == True:
        material = state.get("material", {})
        if material.get("raw_texts") or state.get("ppt_brief"):
            return "freeze_brief_node"
        return "ask_material_node"
    else:
        return "ask_followup_node"

def route_entry(state: State) -> str:
    if state.get("status") == "waiting_confirm":
        return "check_user_confirm_node"

    if state.get("status") == "waiting_material":
        return "collect_material_node"

    return "collect_requirement_node"

def route_confirm(state: State) -> str:
    if state.get("confirmed") == True:
        return "generate_design_spec_node"

    if state.get("status") == "waiting_confirm":
        return "end"

    return "collect_requirement_node"
wf = StateGraph(State)
wf.add_node("check_requirement_node",check_r_node)
wf.add_node("ask_followup_node",ask_f_node)
wf.add_node("ask_material_node",ask_m_node)
wf.add_node("collect_material_node",collect_m_node)
wf.add_node("collect_requirement_node",collect_r_node)
wf.add_node("create_project_node",create_p_node)
wf.add_node("freeze_brief_node",freeze_b_node)
wf.add_node("plan_deck_node",plan_d_node)
wf.add_node("write_project_materials_node",w_p_m_node)
wf.add_node("confirm_plan_node", confirm_p_node)
wf.add_node("check_user_confirm_node", check_u_c_node)
wf.add_node("generate_design_spec_node", generate_d_s_node)
wf.add_node("generate_spec_lock_node", generate_s_l_node)
wf.add_node("generate_svg_node", generate_s_v_g_node)
wf.add_node("export_ppt_node", export_p_node)

wf.add_conditional_edges(
    START,
    route_entry,
    {
        "collect_requirement_node": "collect_requirement_node",
        "check_user_confirm_node": "check_user_confirm_node",
        "collect_material_node": "collect_material_node",
    },
)

wf.add_edge("collect_requirement_node","check_requirement_node")

wf.add_conditional_edges(
    "check_user_confirm_node",
    route_confirm,
    {
        "generate_design_spec_node": "generate_design_spec_node",
        "collect_requirement_node": "collect_requirement_node",
        "end": END,
    },
)

wf.add_conditional_edges(
    "check_requirement_node",
    route
)
wf.add_edge("ask_followup_node",END)
wf.add_edge("ask_material_node",END)
wf.add_edge("collect_material_node","freeze_brief_node")
wf.add_edge("freeze_brief_node","plan_deck_node")
wf.add_edge("plan_deck_node","create_project_node")
wf.add_edge("create_project_node","write_project_materials_node")
wf.add_edge("write_project_materials_node","confirm_plan_node")
wf.add_edge("confirm_plan_node",END)
wf.add_edge("generate_design_spec_node","generate_spec_lock_node")
wf.add_edge("generate_spec_lock_node","generate_svg_node")
wf.add_edge("generate_svg_node","export_ppt_node")
wf.add_edge("export_ppt_node",END)

app = wf.compile()

