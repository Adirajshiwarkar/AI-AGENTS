from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class AgentState:
    """In-memory state container representing the workspace memory of the agent."""
    request: str = ""
    document_type: str = ""
    sections: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    section_contents: Dict[str, str] = field(default_factory=dict)
    reflection_result: Dict[str, Any] = field(default_factory=dict)
    document_path: str = ""
    execution_time: str = ""
    
    def reset(self):
        self.request = ""
        self.document_type = ""
        self.sections = []
        self.assumptions = []
        self.tasks = []
        self.completed_tasks = []
        self.section_contents = {}
        self.reflection_result = {}
        self.document_path = ""
        self.execution_time = ""

    def add_completed_task(self, task: str):
        if task not in self.completed_tasks:
            self.completed_tasks.append(task)

    def get_full_markdown_content(self) -> str:
        """Concatenates all section contents into a single markdown string."""
        md = f"# {self.document_type}\n\n"
        for title, content in self.section_contents.items():
            md += f"## {title}\n\n{content}\n\n"
        return md
