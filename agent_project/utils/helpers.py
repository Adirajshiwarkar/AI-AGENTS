import json
import re
from typing import Any, Dict, Optional
from utils.logger import logger

def clean_json_string(raw_content: str) -> str:
    """Extracts valid JSON substring from LLM response."""
    # Find block wrapped in ```json ... ```
    json_block_match = re.search(r"```json\s*(.*?)\s*```", raw_content, re.DOTALL)
    if json_block_match:
        return json_block_match.group(1).strip()
        
    # Find block wrapped in ``` ... ```
    any_block_match = re.search(r"```\s*(.*?)\s*```", raw_content, re.DOTALL)
    if any_block_match:
        return any_block_match.group(1).strip()
        
    # Fallback to scanning for the first '{' and last '}'
    first_brace = raw_content.find("{")
    last_brace = raw_content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return raw_content[first_brace:last_brace + 1].strip()
        
    return raw_content.strip()

def safe_parse_json(raw_content: str) -> Optional[Dict[str, Any]]:
    """Attempts to clean and parse a JSON string from LLM, logging errors if any."""
    cleaned = clean_json_string(raw_content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}. Raw content length: {len(raw_content)}. Cleaned content: {cleaned[:200]}")
        # Try to fix some common LLM JSON syntax errors (like trailing commas before close braces)
        try:
            # Simple regex to remove trailing commas before closing braces/brackets
            fixed = re.sub(r',\s*([\]}])', r'\1', cleaned)
            return json.loads(fixed)
        except Exception:
            return None
