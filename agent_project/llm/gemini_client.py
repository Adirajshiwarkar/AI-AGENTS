import os
import json
import requests
from llm.llm_factory import LLMProvider
from utils.logger import logger

class GeminiProvider(LLMProvider):
    """Concrete provider for Google Gemini API using native HTTP requests."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.is_simulator = False
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not configured. Initializing Gemini Simulator fallback.")
            self.is_simulator = True

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if self.is_simulator:
            return self._simulate(prompt, system_prompt)


        # Route through local Ollama first to save credits/quota if active
        try:
            ollama_url = "http://localhost:11434/api/chat"
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3").strip()
            ollama_payload = {
                "model": ollama_model,
                "messages": [
                    *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.2}
            }
            response = requests.post(ollama_url, json=ollama_payload, timeout=300)

            if response.status_code == 200:
                res_content = response.json().get("message", {}).get("content", "").strip()
                if res_content:
                    logger.info("Successfully completed request using local Ollama.")
                    return res_content
        except Exception:
            pass

        # Use only the allowed Gemini 2.0 models to avoid 403 errors, prioritizing the cheaper/lighter model
        models = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]
        last_err = None
        import time



        for model in models:
            retries = 3
            for attempt in range(retries):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                    headers = {"Content-Type": "application/json"}
                    
                    payload = {
                        "contents": [
                            {"parts": [{"text": prompt}]}
                        ],
                        "generationConfig": {
                            "maxOutputTokens": 1200,
                            "temperature": 0.2
                        }
                    }

                    
                    if system_prompt:
                        payload["systemInstruction"] = {
                            "parts": [{"text": system_prompt}]
                        }
                        
                    response = requests.post(url, headers=headers, json=payload, timeout=45)
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        candidates = res_json.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                        raise ValueError(f"Unexpected response format from Gemini: {res_json}")
                    elif response.status_code == 429:
                        wait_time = 15.0
                        try:
                            res_json = response.json()
                            error_details = res_json.get("error", {}).get("details", [])
                            for detail in error_details:
                                if "RetryInfo" in detail.get("@type", ""):
                                    delay_str = detail.get("retryDelay", "15s")
                                    if delay_str.endswith("s"):
                                        wait_time = float(delay_str[:-1]) + 1.5
                                    break
                        except Exception:
                            pass
                        logger.warning(f"Gemini API rate limit (429) hit for model {model} (attempt {attempt + 1}/{retries}). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Gemini API returned status code {response.status_code}: {response.text}")
                except Exception as e:
                    if attempt < retries - 1:
                        logger.warning(f"Error occurred on model {model} (attempt {attempt + 1}/{retries}): {e}. Retrying...")
                        time.sleep(5)
                        continue
                    logger.warning(f"Gemini generation failed with model {model}: {e}")
                    last_err = e
                    break
                
        raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


    def _simulate(self, prompt: str, system_prompt: str = "") -> str:
        """Simulated Gemini completions for testing without credentials."""
        prompt_lower = prompt.lower()
        
        # 1. Document Type & Intent Analysis
        if "determine the single most appropriate document type" in prompt_lower or "document type" in prompt_lower:
            doc_type = "Business Proposal"
            if "legacy" in prompt_lower or "erp" in prompt_lower or "migration" in prompt_lower:
                doc_type = "Technical Implementation Plan"
            elif "minutes" in prompt_lower:
                doc_type = "Meeting Minutes"
            elif "sop" in prompt_lower:
                doc_type = "SOP"
            
            return json.dumps({
                "document_type": doc_type,
                "sections": [
                    "Title Page",
                    "Executive Summary",
                    "Objectives",
                    "Background",
                    "Main Content",
                    "Recommendations",
                    "Risks & Mitigations",
                    "Timeline",
                    "Conclusion"
                ]
            })

        # 2. Planning / TODO Generator
        if "generate a prioritized task list" in prompt_lower or "todo list" in prompt_lower:
            return json.dumps({
                "tasks": [
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
            })

        # 3. Assumptions Generator
        if "identify missing parameters" in prompt_lower or "assumptions" in prompt_lower:
            if "erp" in prompt_lower or "microservices" in prompt_lower:
                return json.dumps({
                    "assumptions": [
                        "The engineering team consists of 4 full-stack developers and 1 DevOps engineer.",
                        "The migration will use a strangler fig pattern to minimize downtime of the monolithic ERP.",
                        "A cloud provider like AWS is chosen for microservices deployment, utilizing managed Kubernetes (EKS).",
                        "The budget allows for essential SaaS tooling but prohibits hiring external migration consultants.",
                        "Existing ERP databases can be shared temporarily but will be separated as domain boundaries solidify."
                    ]
                })
            else:
                return json.dumps({
                    "assumptions": [
                        "Stakeholders are aligned on the primary objectives and business drivers.",
                        "No external software integration beyond the AI chatbot is within the initial scope.",
                        "Development and deployment will occur on standard public cloud infrastructure.",
                        "Existing customer support agents will participate in user acceptance testing (UAT)."
                    ]
                })

        # 4. Content Generation
        if "generate a comprehensive, high-quality, professional markdown content" in prompt_lower or "generate content" in prompt_lower:
            section_name = "Section Content"
            for line in prompt.split('\n'):
                if "section" in line.lower() and ":" in line:
                    section_name = line.split(":")[-1].strip()
                    break
            
            return f"""
### {section_name}

This is detailed content generated by Gemini. It contains comprehensive analysis, industry metrics, and actionable items.

#### Highlights
* Highlight 1: The proposed migration lowers runtime and compute costs by 30%.
* Highlight 2: Modern containerization speeds up feature deployments by 3x.
* Highlight 3: Targeted microservices reduce single point of failure (SPOF) risks significantly.

#### Implementation Architecture
1. **API Gateway Layer**: Manages ingress routing, JWT validation, and rate limiting.
2. **Container Platform**: Amazon EKS running Dockerized services with auto-scaling triggers.
3. **Database Per Service**: Ensures microservice autonomy and high schema flexibility.

| Metric | Target Goal | Impact Level |
|---|---|---|
| Latency | <200ms | High |
| Availability | 99.9% | Critical |
| Team Velocity | +20% | Medium |
"""

        # 5. Reflection Check
        if "review this document" in prompt_lower or "pass or fail" in prompt_lower:
            return json.dumps({
                "status": "PASS",
                "missing_sections": [],
                "improvements": [
                    "The document format is robust, but consider adding a glossary of terms for non-technical stakeholders.",
                    "Ensure timeline charts are updated once real resource counts are finalized."
                ]
            })

        # Default fallback text
        return "Simulated content generated successfully by Gemini. The autonomous agent workflow functions properly."
