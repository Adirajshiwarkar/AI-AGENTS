from agent.memory import AgentState
from agent.prompts import REFLECTION_SYSTEM_PROMPT, REFLECTION_USER_PROMPT
from llm.llm_factory import LLMFactory
from utils.logger import logger, log_running_reflection
from utils.helpers import safe_parse_json

class ReflectionAgent:
    """Agent component responsible for quality assurance check (PASS/FAIL) on generated document content."""
    
    def __init__(self, llm_factory: LLMFactory):
        self.llm_factory = llm_factory

    def reflect(self, state: AgentState) -> dict:
        log_running_reflection()
        llm = self.llm_factory.get_client()

        # Build a truncated representation for QA reflection to stay well within token limits
        truncated_content = f"# {state.document_type}\n\n"
        for title, content in state.section_contents.items():
            snippet = content[:400]
            if len(content) > 400:
                snippet += "... [Content Truncated for Token Efficiency]"
            truncated_content += f"## {title}\n{snippet}\n\n"
            
        prompt = REFLECTION_USER_PROMPT.format(
            request=state.request,
            doc_type=state.document_type,
            assumptions=state.assumptions,
            full_document_content=truncated_content
        )

        
        try:
            reflection_raw = llm.generate(prompt, system_prompt=REFLECTION_SYSTEM_PROMPT)
            reflection_data = safe_parse_json(reflection_raw)
            
            if reflection_data and "status" in reflection_data:
                # Normalise status
                status = str(reflection_data["status"]).upper().strip()
                reflection_data["status"] = "PASS" if "PASS" in status else "FAIL"
                
                # Default empty lists if missing
                if "missing_sections" not in reflection_data:
                    reflection_data["missing_sections"] = []
                if "improvements" not in reflection_data:
                    reflection_data["improvements"] = []
                    
                logger.info(f"Reflection complete. Status: {reflection_data['status']}. Missing: {reflection_data['missing_sections']}")
                return reflection_data
            else:
                raise ValueError("Parsed reflection JSON did not contain status field.")
                
        except Exception as e:
            logger.error(f"Reflection LLM query failed: {e}. Defaulting to PASS.")
            return {
                "status": "PASS",
                "missing_sections": [],
                "improvements": ["Could not run reflection analysis due to an upstream LLM error. Defaulting to PASS."]
            }

