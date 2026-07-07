from typing import List, Dict, Any, TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Defines the system state object shared across multi-agent graph nodes.
    Tracks dialogue history, currently assigned worker agent, audit trails, and data inputs.
    """
    # Active user / system message history (appended automatically)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Destination node routing parameter (set by supervisor)
    next_agent: str
    
    # Dictionary storing working memory, API tokens, and temporary files context
    context: Dict[str, Any]
    
    # Trace tracking audit checkpoints
    audit_trail: Annotated[List[Dict[str, Any]], operator.add]
    
    # General execution status (active, completed, error)
    status: str
