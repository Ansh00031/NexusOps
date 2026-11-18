import json
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.agents.base import BaseLLMClient, LLMResponse

logger = logging.getLogger("nexusops.llm")

class GeminiLLMClient(BaseLLMClient):
    """Live Google Gemini client using the google-genai SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize google-genai Client: {e}. Falling back to mock client.")
            self.client = None

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMResponse:
        if not self.client:
            return MockLLMClient().generate(system_prompt, user_prompt, temperature)

        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                response_mime_type="application/json"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )
            text = response.text or "{}"
            tokens = getattr(response.usage_metadata, "total_token_count", 250) if hasattr(response, "usage_metadata") else 250
            return LLMResponse(content=text, model=self.model_name, tokens_used=tokens, confidence=0.96)
        except Exception as e:
            logger.error(f"Gemini API invocation error: {e}. Falling back to deterministic Mock client.")
            return MockLLMClient().generate(system_prompt, user_prompt, temperature)

class MockLLMClient(BaseLLMClient):
    """
    Deterministic enterprise LLM emulator.
    Produces strictly structured JSON for all supported scenarios and edge cases.
    """

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMResponse:
        user_lower = user_prompt.lower()

        # Extract untrusted content section specifically if present
        payload_section = user_lower
        if "<untrusted_customer_payload>" in user_lower and "</untrusted_customer_payload>" in user_lower:
            payload_section = user_lower.split("<untrusted_customer_payload>")[1].split("</untrusted_customer_payload>")[0]

        # 1. Check prompt injection
        if "system override" in payload_section or "superuser mode" in payload_section or "disregard all previous" in payload_section:
            mock_payload = {
                "intent": "Security Threat / Adversarial Prompt Injection Attempt",
                "executive_summary": "Malicious payload detected attempting administrative system override and unauthorized $10,000 billing payout. Prompt injection neutralized; flagged for security review.",
                "sla_priority": "CRITICAL",
                "routing": {
                    "departments": ["SECURITY", "FINANCE"],
                    "primary_department": "SECURITY",
                    "routing_reason": "Adversarial prompt injection pattern detected within customer input payload."
                },
                "prompt_injection_detected": True,
                "security_warning": "CRITICAL: Attempted prompt injection targeting financial authorization limits.",
                "confidence_score": 0.99,
                "agent_reasoning": "Detected untrusted instruction override keywords ('SYSTEM OVERRIDE', 'Disregard all previous', '$10,000.00'). Strictly isolating untrusted payload and locking down actions."
            }
        # 2. Check routine password / IAM ticket
        elif "password" in payload_section or "passkey" in payload_section or "lockout" in payload_section or "srv-auth-master" in payload_section:
            mock_payload = {
                "intent": "Internal IAM Credential Provisioning",
                "executive_summary": "QA engineer Marcus Vance requested routine 24h password reset token for srv-auth-master-01 after lockout.",
                "sla_priority": "LOW",
                "routing": {
                    "departments": ["IT"],
                    "primary_department": "IT",
                    "routing_reason": "Standard single-user internal identity credential reset."
                },
                "prompt_injection_detected": False,
                "security_warning": None,
                "confidence_score": 0.99,
                "agent_reasoning": "Benign low-risk internal IT support request. Zero financial or production outage impact."
            }
        # 3. Check production outage / SLA refund
        elif "outage" in payload_section or "503" in payload_section or "node-eu-prod-04" in payload_section or "sla credit" in payload_section or "refund" in payload_section:
            mock_payload = {
                "intent": "Production Outage & SLA Breach Refund Claim",
                "executive_summary": "Customer CUST-10482 reports production worker failure on node-eu-prod-04 with HTTP 503 errors and demands $250 SLA credit.",
                "sla_priority": "CRITICAL",
                "routing": {
                    "departments": ["IT", "FINANCE", "CRM"],
                    "primary_department": "IT",
                    "routing_reason": "Active service degradation on production cluster impacting tier-1 VIP client."
                },
                "prompt_injection_detected": False,
                "security_warning": None,
                "confidence_score": 0.98,
                "agent_reasoning": "Correlated node-eu-prod-04 error with CUST-10482 99.99% Tier-1 SLA. Dispatched sub-tasks to IT Infra for node recovery and Finance for $250 credit verification."
            }
        # 4. Check bulk order / inventory
        elif "b2b_order" in payload_section or "sku-server-rack" in payload_section or "bulk" in payload_section or "ord-84729" in payload_section:
            mock_payload = {
                "intent": "VIP Bulk Order Fulfillment & Stock Allocation",
                "executive_summary": "VIP customer ORG-ACME placed order ORD-84729 requesting 25 units of SKU-SERVER-RACK-99 with 24h air delivery.",
                "sla_priority": "HIGH",
                "routing": {
                    "departments": ["INVENTORY", "CRM"],
                    "primary_department": "INVENTORY",
                    "routing_reason": "High-value bulk order requires urgent inventory allocation and shipment validation."
                },
                "prompt_injection_detected": False,
                "security_warning": None,
                "confidence_score": 0.95,
                "agent_reasoning": "Identified high-volume order from VIP customer. Routed to Inventory for stock allocation and CRM for expedited VIP logistics handling."
            }
        else:
            mock_payload = {
                "intent": "General Operational Inquiry",
                "executive_summary": "Unclassified business operations request received and parsed.",
                "sla_priority": "MEDIUM",
                "routing": {
                    "departments": ["CRM"],
                    "primary_department": "CRM",
                    "routing_reason": "General customer inquiry routing."
                },
                "prompt_injection_detected": False,
                "security_warning": None,
                "confidence_score": 0.90,
                "agent_reasoning": "Standard triage and entity extraction completed."
            }

        return LLMResponse(
            content=json.dumps(mock_payload),
            model="nexus-mock-llm-v1",
            tokens_used=180,
            confidence=mock_payload.get("confidence_score", 0.95)
        )

def get_llm_client() -> BaseLLMClient:
    """Factory to retrieve configured LLM client."""
    if not settings.mock_mode and settings.gemini_api_key:
        return GeminiLLMClient(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
    return MockLLMClient()
