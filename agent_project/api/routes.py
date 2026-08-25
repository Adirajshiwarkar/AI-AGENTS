import asyncio
import json
import logging
import queue
import threading
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from models.request import AgentRequest
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

class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        # Simple clean message formatter (no date or name prefixes)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

async def stream_agent_workflow(request_text: str):
    log_queue = queue.Queue()
    handler = QueueLogHandler(log_queue)
    handler.setLevel(logging.INFO)
    
    # Add handler to the global logger
    logger.addHandler(handler)
    
    workflow_result = {}
    exception_occurred = None
    
    def worker():
        nonlocal exception_occurred
        try:
            res = workflow.run(request_text)
            workflow_result.update(res)
        except Exception as e:
            exception_occurred = e
            logger.error(f"Worker exception: {e}", exc_info=True)
            
    thread = threading.Thread(target=worker)
    thread.start()
    
    # Read from queue and yield to client in real-time
    while thread.is_alive() or not log_queue.empty():
        try:
            log_msg = log_queue.get_nowait()
            yield json.dumps({"type": "log", "message": log_msg}) + "\n"
        except queue.Empty:
            await asyncio.sleep(0.1)
            
    # Clean up handler
    logger.removeHandler(handler)
    
    if exception_occurred:
        yield json.dumps({"type": "error", "message": str(exception_occurred)}) + "\n"
        return
        
    if workflow_result.get("status") == "error":
        yield json.dumps({"type": "error", "message": workflow_result.get("summary", "Unknown error occurred")}) + "\n"
    else:
        yield json.dumps({"type": "result", "data": workflow_result}) + "\n"

@router.post(
    "/agent", 
    summary="Run Autonomous Business Document Generation Agent with Real-Time Streaming logs",
    description="Accepts a request, plans tasks, generates content, validates it, and streams back NDJSON logs and final result."
)
async def run_agent(payload: AgentRequest):
    logger.info(f"Received API request for streaming: '{payload.request}'")
    return StreamingResponse(
        stream_agent_workflow(payload.request),
        media_type="application/x-ndjson"
    )
