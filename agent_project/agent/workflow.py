import os
import time
from agent.memory import AgentState
from agent.planner import Planner
from agent.executor import Executor
from agent.reflection import ReflectionAgent
from tools.document_generator import DocumentGenerator
from tools.timer import Timer
from tools.validator import DocumentValidator
from llm.llm_factory import LLMFactory
from utils.logger import logger, log_agent_step, log_completed_successfully

class AgentWorkflow:
    """The main orchestrator implementing the autonomous agent flow."""

    def __init__(
        self, 
        llm_factory: LLMFactory,
        planner: Planner,
        executor: Executor,
        reflection_agent: ReflectionAgent,
        doc_generator: DocumentGenerator
    ):
        self.llm_factory = llm_factory
        self.planner = planner
        self.executor = executor
        self.reflection_agent = reflection_agent
        self.doc_generator = doc_generator

    def run(self, request_text: str) -> dict:
        timer = Timer()
        timer.start()

        state = AgentState()
        state.request = request_text

        try:
            # Step 1 & 2: Analyze Intent, generate Assumptions and Planning TODO list
            log_agent_step("Planning Phase", "Analyzing request, document type, and TODO list.")
            state = self.planner.execute_planning(state)

            # Step 3 & 4: Execute each task in the TODO list sequentially (generates content)
            log_agent_step("Execution Phase", f"Running {len(state.tasks)} tasks sequentially.")
            state = self.executor.execute_tasks(state)

            # Step 5: Generate the Word Document (First Draft)
            log_agent_step("Document Generation", "Compiling markdown to styled Word Document.")
            doc_filename = f"{state.document_type.replace(' ', '_').lower()}_{int(time.time())}.docx"
            temp_path = self.doc_generator.generate_docx(
                title=f"{state.document_type} - {request_text[:40]}...",
                sections_content=state.section_contents,
                output_filename=doc_filename
            )
            state.document_path = temp_path

            # Step 6: Reflection & Self-Check
            log_agent_step("Reflection Phase", "Auditing document quality with LLM Self-Check.")
            reflection_result = self.reflection_agent.reflect(state)
            state.reflection_result = reflection_result

            # Engineering Improvement: If QA FAIL, regenerate only the failed/weak sections
            if reflection_result.get("status") == "FAIL":
                failed_sections = reflection_result.get("missing_sections", [])
                if not failed_sections:
                    # If status was FAIL but no sections were explicitly specified, fallback to all
                    failed_sections = state.sections

                log_agent_step("Regeneration Loop", f"Document failed check. Regenerating sections: {failed_sections}")
                state = self.executor.regenerate_failed_sections(state, failed_sections)

                # Re-generate the Word Document with the fixed content
                logger.info("Re-generating final Word Document with updated sections.")
                temp_path = self.doc_generator.generate_docx(
                    title=f"{state.document_type} - {request_text[:40]}...",
                    sections_content=state.section_contents,
                    output_filename=doc_filename
                )
                state.document_path = temp_path

                # Run a quick second reflection verification
                logger.info("Running post-regeneration sanity check.")
                second_reflection = self.reflection_agent.reflect(state)
                # Ensure the status is updated to represent the improvement
                state.reflection_result = second_reflection

            # Step 7: Validate that the file is generated, exists, and is non-empty
            log_agent_step("Verification", "Validating final document file status.")
            valid = DocumentValidator.validate_file_exists_and_not_empty(state.document_path)
            if not valid:
                raise RuntimeError("Generated Word Document failed physical file validation.")

            # Step 8: Generate short document summary for the JSON response
            summary = self._generate_brief_summary(state)
            
            # Stop timer
            timer.stop()
            state.execution_time = timer.get_duration_str()
            log_completed_successfully()

            # Prepare structured response dictionary
            return {
                "status": "success",
                "summary": summary,
                "execution_plan": state.tasks,
                "completed_tasks": state.completed_tasks,
                "document_path": state.document_path,
                "document_location": state.document_path,  # Provided for strict output format compatibility
                "assumptions": state.assumptions,
                "reflection_result": state.reflection_result,
                "execution_time": state.execution_time,
                "sections_content": state.section_contents
            }

        except Exception as e:
            timer.stop()
            logger.critical(f"Agent workflow collapsed: {e}", exc_info=True)
            return {
                "status": "error",
                "summary": f"Failed to complete workflow: {str(e)}",
                "execution_plan": state.tasks,
                "completed_tasks": state.completed_tasks,
                "document_path": state.document_path if state.document_path else "",
                "document_location": state.document_path if state.document_path else "",
                "assumptions": state.assumptions,
                "reflection_result": {
                    "status": "FAIL",
                    "missing_sections": [],
                    "improvements": [f"Execution interrupted by error: {str(e)}"]
                },
                "execution_time": timer.get_duration_str(),
                "sections_content": state.section_contents if hasattr(state, "section_contents") else {}
            }

    def _generate_brief_summary(self, state: AgentState) -> str:
        """Invokes the LLM to generate a quick two-sentence summary of the generated content."""
        logger.info("Generating final brief document summary...")
        prompt = f"""
Summarize the following document details in exactly two professional, concise sentences.
Document Type: {state.document_type}
Assumptions: {state.assumptions}
Sections: {list(state.section_contents.keys())}
Request context: {state.request}
"""
        try:
            llm = self.llm_factory.get_client()
            summary_text = llm.generate(prompt).strip()
            return summary_text
        except Exception as e:
            logger.warning(f"Failed to generate custom summary: {e}. Using fallback summary.")
            return f"Successfully generated a professional {state.document_type} docx document containing {len(state.section_contents)} sections based on the request."
