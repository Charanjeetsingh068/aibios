from typing import Any, Dict, List, Literal, TypedDict
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    next_node: str
    user_context: Dict[str, Any]


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Inspects context and schedules the next workflow destination agent."""
    last_message = state["messages"][-1]["content"].lower() if state["messages"] else ""
    
    if "lead" in last_message or "sales" in last_message or "pricing" in last_message:
        next_node = "sales_agent"
    elif "kb" in last_message or "help" in last_message or "documentation" in last_message:
        next_node = "knowledge_agent"
    elif "trigger" in last_message or "workflow" in last_message or "automation" in last_message:
        next_node = "automation_agent"
    else:
        next_node = END
        
    return {"next_node": next_node}


def sales_agent_node(state: AgentState) -> Dict[str, Any]:
    messages = list(state["messages"])
    messages.append({
        "role": "assistant",
        "content": "[Sales Agent] Processing CRM lead qualification checklist and routing value opportunities."
    })
    return {"messages": messages, "next_node": END}


def knowledge_agent_node(state: AgentState) -> Dict[str, Any]:
    messages = list(state["messages"])
    messages.append({
        "role": "assistant",
        "content": "[Knowledge Agent] Searching vector collections index for relevant guides."
    })
    return {"messages": messages, "next_node": END}


def automation_agent_node(state: AgentState) -> Dict[str, Any]:
    messages = list(state["messages"])
    messages.append({
        "role": "assistant",
        "content": "[Automation Agent] Running conditional workflow trigger scripts."
    })
    return {"messages": messages, "next_node": END}


def should_continue(state: AgentState) -> Literal["sales_agent", "knowledge_agent", "automation_agent", "__end__"]:
    val = state["next_node"]
    if val == "sales_agent":
        return "sales_agent"
    elif val == "knowledge_agent":
        return "knowledge_agent"
    elif val == "automation_agent":
        return "automation_agent"
    return END


workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sales_agent", sales_agent_node)
workflow.add_node("knowledge_agent", knowledge_agent_node)
workflow.add_node("automation_agent", automation_agent_node)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    should_continue,
    {
        "sales_agent": "sales_agent",
        "knowledge_agent": "knowledge_agent",
        "automation_agent": "automation_agent",
        "__end__": END
    }
)

compiled_graph = workflow.compile()
