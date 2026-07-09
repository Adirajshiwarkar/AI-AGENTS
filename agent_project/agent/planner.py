from agent.memory import AgentState
from agent.prompts import INTENT_SYSTEM_PROMPT, INTENT_USER_PROMPT, PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT
from tools.assumption_engine import AssumptionEngine
from llm.llm_factory import LLMFactory
from utils.logger import logger, log_planning, log_creating_todo
from utils.helpers import safe_parse_json

class Planner:
    """Agent component responsible for analyzing intent, formulating assumptions, and generating a TODO plan."""
    
    def __init__(self, llm_factory: LLMFactory, assumption_engine: AssumptionEngine):
        self.llm_factory = llm_factory
        self.assumption_engine = assumption_engine

    def execute_planning(self, state: AgentState) -> AgentState:
        log_planning()
        llm = self.llm_factory.get_client()

        # Step 1: Analyze Intent and Document Type
        logger.info("Analyzing user intent and document type...")
        intent_prompt = INTENT_USER_PROMPT.format(request=state.request)
        try:
            intent_raw = llm.generate(intent_prompt, system_prompt=INTENT_SYSTEM_PROMPT)
            intent_data = safe_parse_json(intent_raw)
            if intent_data and "document_type" in intent_data and "sections" in intent_data:
                state.document_type = intent_data["document_type"]
                state.sections = intent_data["sections"]
            else:
                raise ValueError("Parsed intent JSON did not contain necessary fields.")
        except Exception as e:
            logger.error(f"Intent analysis LLM query failed: {e}. Using generic fallback.")
            state.document_type = "Business Report"
            state.sections = [
                "Executive Summary", 
                "Objectives", 
                "Background", 
                "Main Content", 
                "Recommendations", 
                "Risks & Mitigations", 
                "Timeline", 
                "Conclusion"
            ]

        logger.info(f"Identified Document Type: {state.document_type}")
        logger.info(f"Required Sections: {state.sections}")

        # Step 2: Create Assumptions
        logger.info("Triggering assumption engine...")
        state.assumptions = self.assumption_engine.generate_assumptions(state.request, state.document_type)

        # Step 3: Create TODO Task List
        log_creating_todo()
        planner_prompt = PLANNER_USER_PROMPT.format(
            request=state.request,
            doc_type=state.document_type,
            sections=state.sections,
            assumptions=state.assumptions
        )
        try:
            planner_raw = llm.generate(planner_prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
            planner_data = safe_parse_json(planner_raw)
            if planner_data and "tasks" in planner_data and isinstance(planner_data["tasks"], list):
                state.tasks = [str(t) for t in planner_data["tasks"]]
            else:
                raise ValueError("Parsed planner JSON did not contain tasks array.")
        except Exception as e:
            logger.error(f"Task generation LLM query failed: {e}. Using fallback checklist.")
            state.tasks = [
                "Understand request",
                "Extract objectives",
                "Identify document type",
                "Determine required sections",
                "Create assumptions",
                "Generate outline",
                "Generate content",
                "Format document",
                "Validate document",
                "Reflect and improve"
            ]

        logger.info(f"Generated task plan: {state.tasks}")
        return state
