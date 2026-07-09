from fastapi import APIRouter, HTTPException, status
from models.request import AgentRequest
from models.response import AgentResponse
from agent.workflow import AgentWorkflow
from agent.planner import Planner
from agent.executor import Executor
from agent.reflection import ReflectionAgent
from tools.document_generator import DocumentGenerator
from tools.assumption_engine import AssumptionEngine
from llm.llm_factory import LLMFactory
from utils.logger import logger

router = APIRouter()

# Instantiate the LLM components and Agent services
llm_factory = LLMFactory()
assumption_engine = AssumptionEngine(llm_factory)
planner = Planner(llm_factory, assumption_engine)
executor = Executor(llm_factory)
reflection_agent = ReflectionAgent(llm_factory)
doc_generator = DocumentGenerator()

# Instantiate workflow orchestrator
workflow = AgentWorkflow(
    llm_factory=llm_factory,
    planner=planner,
    executor=executor,
    reflection_agent=reflection_agent,
    doc_generator=doc_generator
)

@router.post(
    "/agent", 
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Autonomous Business Document Generation Agent",
    description="Accepts a natural language query, plans tasks, generates content, validates it, and outputs a professional DOCX."
)
async def run_agent(payload: AgentRequest):
    logger.info(f"Received API request: '{payload.request}'")
    
    # Run the orchestrator workflow
    result = workflow.run(payload.request)
    
    if result.get("status") == "error":
        logger.error(f"API request failed during execution: {result.get('summary')}")
        # Return structured error response or raise HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )
        
    return result
