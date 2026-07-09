from typing import List
from llm.llm_factory import LLMFactory
from utils.logger import logger
from utils.helpers import safe_parse_json

class AssumptionEngine:
    def __init__(self, llm_factory: LLMFactory):
        self.llm_factory = llm_factory

    def generate_assumptions(self, request: str, doc_type: str) -> List[str]:
        """Queries the LLM to generate logical assumptions for the document context."""
        logger.info(f"Generating assumptions for request of type: {doc_type}")
        
        prompt = f"""
You are an expert business analyst and technical architect.
Analyze the following request for a {doc_type} document and identify missing parameters or gaps.
Generate a list of 4-6 realistic, sensible business and technical assumptions that are critical to making this implementation successful, especially regarding timeline, budget, team size, technical stack, or organizational constraints.

Request: "{request}"

Output MUST be a JSON object containing a list of strings called "assumptions".
Format:
```json
{{
  "assumptions": [
    "Assumption 1...",
    "Assumption 2..."
  ]
}}
```
"""
        try:
            llm = self.llm_factory.get_client()
            response = llm.generate(prompt)
            data = safe_parse_json(response)
            if data and "assumptions" in data and isinstance(data["assumptions"], list):
                assumptions = [str(a) for a in data["assumptions"]]
                logger.info(f"Successfully generated assumptions: {assumptions}")
                return assumptions
        except Exception as e:
            logger.error(f"Failed to generate assumptions using LLM: {e}")

        # Fallback default assumptions based on document type
        logger.warning("Using fallback assumptions due to LLM failure or parse failure.")
        return [
            "The project has senior stakeholder support and sponsorship.",
            "Standard organizational resources and collaboration platforms are available.",
            "The initial phase will focus on high-impact MVP components.",
            "Subject matter experts will be available for validation sessions as needed."
        ]
