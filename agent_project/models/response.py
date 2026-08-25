from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AgentResponse(BaseModel):
    status: str
    summary: str
    execution_plan: List[str]
    completed_tasks: List[str]
    document_path: str
    document_location: str  # Kept to satisfy both requirements
    assumptions: List[str]
    reflection_result: Dict[str, Any]
    execution_time: str
    sections_content: Optional[Dict[str, str]] = None

