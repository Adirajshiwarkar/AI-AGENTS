import os
import sys
import time
from dotenv import load_dotenv

# Ensure current directory is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.workflow import AgentWorkflow
from agent.planner import Planner
from agent.executor import Executor
from agent.reflection import ReflectionAgent
from tools.document_generator import DocumentGenerator
from tools.assumption_engine import AssumptionEngine
from llm.llm_factory import LLMFactory
from utils.logger import logger

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    llm_factory = LLMFactory()
    assumption_engine = AssumptionEngine(llm_factory)
    planner = Planner(llm_factory, assumption_engine)
    executor = Executor(llm_factory)
    reflection_agent = ReflectionAgent(llm_factory)
    doc_generator = DocumentGenerator()
    
    workflow = AgentWorkflow(
        llm_factory=llm_factory,
        planner=planner,
        executor=executor,
        reflection_agent=reflection_agent,
        doc_generator=doc_generator
    )
    
    print("\n" + "="*60)
    print("      AUTONOMOUS AI BUSINESS DOCUMENT GENERATOR CLI      ")
    print("="*60)
    print("Configure your Groq API key in .env to run with live LLM.")
    print("Press Ctrl+C at any time to exit.\n")
    
    while True:
        try:
            query = input("Enter your document request: ").strip()
            
            # Simple validation
            if not query:
                print("Error: Request cannot be empty. Please try again.\n")
                continue
            if len(query) < 10:
                print("Error: Request is too short. Please provide a descriptive prompt (min 10 chars).\n")
                continue
                
            print("\n" + "-"*50)
            print(f"Processing Query: '{query}'")
            print("-"*50 + "\n")
            
            start_time = time.time()
            result = workflow.run(query)
            duration = time.time() - start_time
            
            print("\n" + "="*50)
            print("                 EXECUTION SUMMARY                ")
            print("="*50)
            if result.get("status") == "success":
                print(f"Status:             SUCCESS")
                print(f"Summary:            {result.get('summary')}")
                print(f"Execution Time:     {duration:.2f} seconds")
                print(f"Document Path:      {result.get('document_path')}")
                print(f"Assumptions Made:   {len(result.get('assumptions', []))}")
                for idx, assumption in enumerate(result.get('assumptions', []), 1):
                    print(f"  {idx}. {assumption}")
                print(f"Reflection Result:  {result.get('reflection_result', {}).get('status', 'N/A')}")
            else:
                print(f"Status:             FAILED")
                print(f"Error Summary:      {result.get('summary')}")
                print(f"Execution Time:     {duration:.2f} seconds")
            print("="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting CLI. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Unexpected error in CLI loop: {e}", exc_info=True)
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()
