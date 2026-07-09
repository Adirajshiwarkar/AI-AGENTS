from agent.memory import AgentState
from agent.prompts import CONTENT_GENERATOR_SYSTEM_PROMPT, CONTENT_GENERATOR_USER_PROMPT
from llm.llm_factory import LLMFactory
from utils.logger import logger, log_executing_task

class Executor:
    """Agent component responsible for sequentially executing the plan and generating document content."""
    
    def __init__(self, llm_factory: LLMFactory):
        self.llm_factory = llm_factory

    def execute_tasks(self, state: AgentState) -> AgentState:
        llm = self.llm_factory.get_client()

        # Step 1: Iterate through and execute planned tasks
        for idx, task in enumerate(state.tasks, 1):
            log_executing_task(idx, task)
            
            # Execute logic depending on the task type
            task_lower = task.lower()
            
            if "generate content" in task_lower or "generate outline" in task_lower:
                # Perform the core section content generation
                state = self._generate_all_sections(state, llm)
            elif "format document" in task_lower or "create document" in task_lower:
                # Format document step is registered; actual DOCX generation is called in workflow,
                # but we can log that we are preparing styles and layouts.
                logger.info("Preparing formatting styles, typography, and page numbers.")
            elif "validate" in task_lower:
                logger.info("Initiating structural and file presence checks.")
            elif "reflect" in task_lower or "improve" in task_lower:
                logger.info("Readying quality assurance (QA) reflection pipeline.")
            else:
                # Simulated tasks (like Understand Request, Extract Objectives, etc.)
                logger.info(f"Task '{task}' executed successfully.")
                
            state.add_completed_task(task)

        return state

    def _generate_all_sections(self, state: AgentState, llm) -> AgentState:
        """Helper to generate content for each structural section of the document."""
        logger.info(f"Generating content for {len(state.sections)} sections...")
        
        previous_context = ""
        import time
        for idx, section in enumerate(state.sections):
            # Space out requests to stay strictly under free tier rate limits (15 RPM) only for Gemini
            import os
            if idx > 0 and os.getenv("LLM_PROVIDER", "").strip().lower() == "gemini":
                logger.info("Pausing for 4.5 seconds to respect Gemini API rate limits...")
                time.sleep(4.5)


            logger.info(f"Generating section: {section}")
            
            prompt = CONTENT_GENERATOR_USER_PROMPT.format(
                request=state.request,
                doc_type=state.document_type,
                assumptions=state.assumptions,
                section_name=section,
                previous_context=previous_context if previous_context else "None (First Section)"
            )
            
            try:
                section_content = llm.generate(prompt, system_prompt=CONTENT_GENERATOR_SYSTEM_PROMPT)
                state.section_contents[section] = section_content

                
                # Rolling window context: titles of all sections generated so far + full content of the last one
                titles_str = ", ".join(state.sections[:idx+1])
                previous_context = f"Generated sections so far: {titles_str}\n\nLast section content:\n### {section}\n{section_content}\n"
            except Exception as e:
                logger.error(f"Failed to generate section {section}: {e}")
                state.section_contents[section] = f"Content generation for section {section} failed due to an upstream LLM error."
                
        return state

    def regenerate_failed_sections(self, state: AgentState, failed_sections: list) -> AgentState:
        """Targeted regeneration of sections that failed quality reflection check."""
        llm = self.llm_factory.get_client()
        logger.info(f"Regenerating failed sections: {failed_sections}")

        for section in failed_sections:
            logger.info(f"Regenerating section: {section}")
            
            # Reconstruct previous context: titles of preceding sections + content of the section right before
            generated_so_far = []
            prev_s = None
            for s in state.sections:
                if s == section:
                    break
                generated_so_far.append(s)
                if s in state.section_contents:
                    prev_s = s
                    
            titles_str = ", ".join(generated_so_far)
            last_content = state.section_contents[prev_s] if prev_s and prev_s in state.section_contents else "None"
            previous_context = f"Generated sections so far: {titles_str}\n\nLast section content:\n### {prev_s or 'None'}\n{last_content}\n"
            
            prompt = CONTENT_GENERATOR_USER_PROMPT.format(
                request=state.request,
                doc_type=state.document_type,
                assumptions=state.assumptions,
                section_name=section,
                previous_context=previous_context
            )

            
            try:
                regenerated_content = llm.generate(prompt, system_prompt=CONTENT_GENERATOR_SYSTEM_PROMPT)
                state.section_contents[section] = regenerated_content
                logger.info(f"Successfully regenerated section: {section}")
            except Exception as e:
                logger.error(f"Failed to regenerate section {section}: {e}")
                
        return state
