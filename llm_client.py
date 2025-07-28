"""LLM client for generating responses using OpenAI or Anthropic APIs."""

import asyncio
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

import httpx  # added for custom client with Anthropic
import openai
import anthropic
from loguru import logger

from config import settings


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response from the LLM."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response using OpenAI's API."""
        try:
            formatted_messages = []
            
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            
            formatted_messages.extend(messages)
            
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=formatted_messages,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


# --- Updated to supply our own httpx client (new httpx>=0.28 no longer supports
#     the deprecated `proxies=` argument that Anthropic passes by default). By
#     giving an `http_client` ourselves we bypass that inner logic and maintain
#     compatibility without downgrading httpx.


class AnthropicClient(LLMClient):
    """Anthropic API client."""

    def __init__(self):
        # Provide a plain AsyncClient so Anthropic doesn't construct one with the
        # obsolete `proxies` kwarg.
        self._httpx_client = httpx.AsyncClient()
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            http_client=self._httpx_client,
        )
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response using Anthropic's API."""
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                if msg["role"] in ["user", "assistant"]:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Use Messages API (recommended by Anthropic)
            response = await self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                system=system_prompt or "You are a helpful assistant.",
                messages=anthropic_messages,
            )
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def aclose(self):
        """Cleanly close the underlying httpx client when done."""
        await self._httpx_client.aclose()


class LLMManager:
    """Manager class for LLM operations."""
    
    def __init__(self):
        self.client = self._create_client()
    
    def _create_client(self) -> LLMClient:
        """Create the appropriate LLM client based on configuration."""
        if settings.default_llm_provider == "openai":
            return OpenAIClient()
        elif settings.default_llm_provider == "anthropic":
            return AnthropicClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.default_llm_provider}")
    
    async def generate_whatsapp_response(
        self, 
        incoming_message: str,
        sender_name: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate a WhatsApp response based on incoming message and context."""
        
        system_prompt = """You are called Matthew, and you are answering your WhatsApp messages. 
        Generate appropriate, concise, and helpful responses. 
        Keep responses conversational and friendly.
        If you're unsure about something, ask for clarification.
        Avoid overly long responses - WhatsApp messages should be brief.
        Do not use multple paragraphs, as these will send as multiple messages.
        Also, do not include extra text like 'friendly reply', etc, as this will be sent as a message."""

        messages = conversation_history or []
        messages.append({
            "role": "user", 
            "content": f"From {sender_name}: {incoming_message}"
        })
        
        return await self.client.generate_response(messages, system_prompt)
    
    async def analyze_message_intent(self, message: str) -> Dict[str, Any]:
        """Analyze the intent and sentiment of a message."""
        
        system_prompt = """Analyze the following WhatsApp message and return a JSON response with:
        - intent: the main purpose (question, request, greeting, complaint, etc.)
        - sentiment: positive, negative, or neutral
        - priority: low, medium, or high
        - requires_response: true/false
        - key_topics: list of main topics mentioned
        
        Only return valid JSON."""
        
        messages = [{"role": "user", "content": message}]
        
        response = await self.client.generate_response(messages, system_prompt)
        
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse intent analysis response: {response}")
            return {
                "intent": "unknown",
                "sentiment": "neutral", 
                "priority": "medium",
                "requires_response": True,
                "key_topics": []
            } 