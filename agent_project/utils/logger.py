import logging
import os
import sys

# ANSI Colors
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_MAGENTA = "\033[35m"

class CustomFormatter(logging.Formatter):
    """Custom logging formatter to add colors based on log level."""
    
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: COLOR_CYAN + format_str + COLOR_RESET,
        logging.INFO: COLOR_RESET + format_str + COLOR_RESET,
        logging.WARNING: COLOR_YELLOW + format_str + COLOR_RESET,
        logging.ERROR: COLOR_RED + format_str + COLOR_RESET,
        logging.CRITICAL: COLOR_BOLD + COLOR_RED + format_str + COLOR_RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.format_str)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logger(name: str = "agent_logger") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)

    # File handler
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/agent.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Primary logger instance
logger = setup_logger()

# Helper terminal logs for agent execution steps (Bonus Requirement)
def log_agent_step(step_name: str, message: str = ""):
    """Prints beautiful colored step progress to the terminal."""
    prefix = f"{COLOR_BOLD}{COLOR_MAGENTA}=== AGENT STEP: {step_name} ==={COLOR_RESET}"
    if message:
        print(f"{prefix} - {COLOR_CYAN}{message}{COLOR_RESET}", flush=True)
    else:
        print(f"{prefix}", flush=True)
    logger.info(f"[STEP] {step_name} - {message}")

def log_planning():
    print(f"\n{COLOR_BOLD}{COLOR_YELLOW}Planning...{COLOR_RESET}", flush=True)
    logger.info("Planning process started.")

def log_creating_todo():
    print(f"{COLOR_BOLD}{COLOR_YELLOW}Creating TODO...{COLOR_RESET}", flush=True)
    logger.info("TODO list creation started.")

def log_executing_task(task_num: int, task_name: str):
    print(f"{COLOR_BOLD}{COLOR_CYAN}Executing Task {task_num}: {task_name}...{COLOR_RESET}", flush=True)
    logger.info(f"Executing Task {task_num}: {task_name}")

def log_generating_docx():
    print(f"{COLOR_BOLD}{COLOR_GREEN}Generating DOCX...{COLOR_RESET}", flush=True)
    logger.info("Document generation started.")

def log_running_reflection():
    print(f"{COLOR_BOLD}{COLOR_YELLOW}Running Reflection...{COLOR_RESET}", flush=True)
    logger.info("Self-reflection process started.")

def log_completed_successfully():
    print(f"{COLOR_BOLD}{COLOR_GREEN}Completed Successfully{COLOR_RESET}\n", flush=True)
    logger.info("Execution completed successfully.")
