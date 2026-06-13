import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class LLMSettings:
    enabled: bool = os.getenv("LLM_ENABLED", "true").lower() == "true"
    provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "900"))
    max_history_messages: int = int(os.getenv("LLM_MAX_HISTORY", "10"))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    chroma_persist_path: str = os.getenv("CHROMA_PERSIST_PATH", "")
    faiss_persist_path: str = os.getenv("FAISS_PERSIST_PATH", "")
    vector_backend: str = os.getenv("VECTOR_BACKEND", "auto")  # auto | chromadb | faiss
    use_llm_intent_router: bool = os.getenv("USE_LLM_INTENT_ROUTER", "true").lower() == "true"

    @property
    def api_key(self) -> str:
        p = self.provider.lower()
        if p == "google" or p == "gemini":
            return self.gemini_api_key
        elif p == "groq":
            return self.groq_api_key
        return self.openai_api_key

    @property
    def model(self) -> str:
        env_model = os.getenv("LLM_MODEL", "")
        if env_model:
            return env_model
        p = self.provider.lower()
        if p == "google" or p == "gemini":
            return "gemini-2.5-flash"
        elif p == "groq":
            return "llama-3.3-70b-versatile"
        return "gpt-4o-mini"

    @property
    def router_model(self) -> str:
        env_router_model = os.getenv("LLM_ROUTER_MODEL", "")
        if env_router_model:
            return env_router_model
        return self.model

    @property
    def base_url(self) -> str | None:
        p = self.provider.lower()
        if p == "google" or p == "gemini":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif p == "groq":
            return "https://api.groq.com/openai/v1"
        return None


llm_settings = LLMSettings()
