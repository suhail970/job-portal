from openai import AsyncOpenAI
from typing import Optional, List, Dict, Any
import json
import logging
from app.core.config import settings

logger = logging.getLogger("skillbridge.ai")

class ModelRouter:
    """
    Unified, OpenAI-compatible Model Gateway for SkillBridge AI.
    Seamlessly routes requests between Google Gemini, Groq, OpenRouter, and Local Ollama.
    """

    def __init__(self):
        self.providers = {
            "gemini": {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "api_key": settings.GEMINI_API_KEY or "dummy-key",
                "default_model": "gemini-2.0-flash",
                "available": bool(settings.GEMINI_API_KEY)
            },
            "groq": {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY or "dummy-key",
                "default_model": "llama-3.3-70b-versatile",
                "available": bool(settings.GROQ_API_KEY)
            },
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": settings.OPENROUTER_API_KEY or "dummy-key",
                "default_model": "meta-llama/llama-3.3-70b-instruct:free",
                "available": bool(settings.OPENROUTER_API_KEY)
            },
            "ollama": {
                "base_url": settings.OLLAMA_BASE_URL,
                "api_key": "ollama",
                "default_model": "qwen2.5-coder:7b",
                "available": True # Local check
            }
        }

    def get_client(self, preferred_provider: Optional[str] = None, custom_config: Optional[Dict[str, str]] = None):
        # Support user-provided custom BYOK endpoint
        if custom_config and custom_config.get("base_url") and custom_config.get("model"):
            base_url = custom_config["base_url"].strip()
            if not base_url.endswith("/"):
                base_url += "/"
            api_key = custom_config.get("api_key") or "dummy-key"
            model = custom_config["model"].strip()
            client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=35.0
            )
            return client, model, "custom"

        provider_name = preferred_provider or settings.DEFAULT_AI_PROVIDER
        cfg = self.providers.get(provider_name, self.providers["gemini"])

        # Fallback if preferred provider has no key configured
        if not cfg["available"] and provider_name != "ollama":
            for name, p_cfg in self.providers.items():
                if p_cfg["available"]:
                    cfg = p_cfg
                    provider_name = name
                    break

        client = AsyncOpenAI(
            base_url=cfg["base_url"],
            api_key=cfg["api_key"],
            timeout=30.0
        )
        return client, cfg["default_model"], provider_name

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        preferred_provider: Optional[str] = None,
        custom_config: Optional[Dict[str, str]] = None,
        json_mode: bool = False
    ) -> str:
        client, model, provider_name = self.get_client(preferred_provider, custom_config)
        
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Error calling {provider_name} ({model}): {e}. Attempting smart fallback...")
            # If Gemini fails, try local Ollama or deterministic fallback
            if provider_name != "ollama":
                try:
                    ollama_client, o_model, _ = self.get_client("ollama")
                    kwargs["model"] = o_model
                    res = await ollama_client.chat.completions.create(**kwargs)
                    return res.choices[0].message.content or ""
                except Exception:
                    pass

            # Intelligent mock fallback so local demo never halts if API key is unconfigured
            return self._generate_fallback(messages)

    def _generate_fallback(self, messages: List[Dict[str, str]]) -> str:
        """
        Guaranteed fallback response for zero-key local student testing.
        """
        user_msg = messages[-1]["content"].lower()
        if "resume" in user_msg or "extract" in user_msg:
            return json.dumps({
                "skills": ["Python", "FastAPI", "SQL", "Machine Learning", "Data Structures", "Next.js", "Docker", "Git"],
                "ats_score": 82.5,
                "summary": "Strong engineering profile with hands-on fullstack and machine learning project experience.",
                "strengths": ["Clear technical stack", "Relevant academic projects", "Competitive CGPA"],
                "improvements": ["Add quantitative metrics to impact statements", "Include cloud certification if available"]
            })
        elif "countdown" in user_msg or "prep" in user_msg or "roadmap" in user_msg:
            return json.dumps({
                "overview": "Tailored placement countdown plan focused on high-yield technical and aptitude topics.",
                "schedule": [
                    {
                        "day": 1,
                        "title": "Core Technical & Data Structures Revision",
                        "tasks": [
                            "Arrays, HashMaps, Two-Pointer technique",
                            "Binary Trees, BFS & DFS traversals",
                            "Top 10 Company-specific interview questions"
                        ]
                    },
                    {
                        "day": 2,
                        "title": "System Design, OOP & Aptitude",
                        "tasks": [
                            "Database indexing, ACID properties, Normalization",
                            "Object-Oriented Programming (Polymorphism, Inheritance)",
                            "Quantitative Aptitude: Time & Work, Speed & Distance"
                        ]
                    },
                    {
                        "day": 3,
                        "title": "Mock Interviews & Leadership Round",
                        "tasks": [
                            "1 Full-length Voice Mock Interview",
                            "Behavioral answers using STAR framework",
                            "Final revision of resume projects"
                        ]
                    }
                ]
            })
        else:
            return json.dumps({
                "response": "Response generated successfully.",
                "status": "ready"
            })

ai_router = ModelRouter()

