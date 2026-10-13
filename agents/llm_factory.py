"""
Deterministic mock responder for synthetic demonstrations; no external LLM providers.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Lung Rads Nodule Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock responder]: This is a test response, not a guideline assessment or clinical verification. Query preview: '{prompt[:60]}...'"


class LLMFactory:
    """Creates the deterministic mock responder with identifier screening."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Lung Rads Nodule Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError("Only the deterministic mock provider is implemented; no LLM service is connected.")
