from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: int = 0
    confidence: float = 0.95

class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMResponse:
        """Generate response from LLM."""
        pass
