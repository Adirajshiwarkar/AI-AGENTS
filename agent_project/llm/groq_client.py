import os
import json
from llm.llm_factory import LLMProvider
from utils.logger import logger

class GroqProvider(LLMProvider):
    """Concrete provider for Groq Cloud API, with a fallback simulator mode if credentials are missing."""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.is_simulator = False
        
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is not configured. Initializing Groq Simulator fallback.")
            self.is_simulator = True
            return

        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            logger.warning("groq library is not installed. Initializing Groq Simulator fallback.")
            self.is_simulator = True

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if self.is_simulator:
            return self._simulate(prompt, system_prompt)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try multiple models to maximize stability
        models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"]
        last_err = None



        
        for model in models:
            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=4096
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq generation failed with model {model}: {e}. Trying next model...")
                last_err = e
                
        raise RuntimeError(f"All Groq models failed. Last error: {last_err}")

    def _simulate(self, prompt: str, system_prompt: str = "") -> str:
        """Simulated Groq completions for testing without credentials."""
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

This is detailed content generated by Groq. It contains comprehensive analysis, industry metrics, and actionable items.

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
        return "Simulated content generated successfully by Groq. The autonomous agent workflow functions properly."
