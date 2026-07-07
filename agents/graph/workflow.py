from typing import Dict, Any
from langgraph.graph import StateGraph, END
from agents.graph.state import AgentState

# ==============================================================================
# Node Execution Stubs
# ==============================================================================

async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Decides routing path based on instruction context.
    Evaluates inputs and determines the next target worker node.
    """
    # Placeholder routing decision logic
    messages = state.get("messages", [])
    last_msg = messages[-1].content.lower() if messages else ""
    
    next_agent = "end"
    if "crm" in last_msg or "customer" in last_msg:
        next_agent = "crm_agent"
    elif "sql" in last_msg or "data" in last_msg or "select" in last_msg:
        next_agent = "db_agent"
        
    return {
        "next_agent": next_agent,
        "audit_trail": [{"node": "supervisor", "status": f"routed_to:{next_agent}"}]
    }

async def crm_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Stub worker node dedicated to CRM and contact information operations.
    """
    return {
        "messages": [{"role": "assistant", "content": "[CRM Agent Stub] Checked contacts successfully."}],
        "next_agent": "supervisor",
        "audit_trail": [{"node": "crm_agent", "status": "processed"}]
    }

async def db_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Stub worker node dedicated to database query and mapping operations.
    """
    return {
        "messages": [{"role": "assistant", "content": "[DB Agent Stub] Query executed on target schema."}],
        "next_agent": "supervisor",
        "audit_trail": [{"node": "db_agent", "status": "processed"}]
    }

# ==============================================================================
# Graph Orchestration Setup
# ==============================================================================

# Initialize State Graph
builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("crm_agent", crm_agent_node)
builder.add_node("db_agent", db_agent_node)

# Set Entry Point
builder.set_entry_point("supervisor")

# Routing Condition
def route_next(state: AgentState) -> str:
    """Evaluates next_agent status to direct workflow transitions."""
    next_dest = state.get("next_agent", "end")
    if next_dest in ["crm_agent", "db_agent"]:
        return next_dest
    return "end"

# Add Conditional Edges
builder.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "crm_agent": "crm_agent",
        "db_agent": "db_agent",
        "end": END
    }
)

# Connect Worker nodes back to Supervisor for validation
builder.add_edge("crm_agent", "supervisor")
builder.add_edge("db_agent", "supervisor")

# Compile Graph
graph = builder.compile()
