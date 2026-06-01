import os
from typing import AsyncGenerator, List, Dict
from openai import AsyncOpenAI
from app.config import settings
from app.utils.helpers import setup_logging

logger = setup_logging()


class LLMService:
    """LLM Service using OpenRouter"""

    def __init__(self):
        self.client = None
        self.is_initialized = False

        # Load from .env
        self.api_key = settings.openrouter_api_key

        self.base_url = "https://openrouter.ai/api/v1"

        self.model = settings.llm_model

    async def initialize(self):
        """Initialize OpenRouter client"""
        try:
            if not self.api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY not found in .env file"
                )

            logger.info(
                f"Loaded OpenRouter key: {self.api_key[:12]}..."
            )

            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=60.0,
                max_retries=2
            )

            self.is_initialized = True

            logger.info(
                f"LLM service initialized with {self.model} via OpenRouter"
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize LLM service: {str(e)}"
            )
            self.is_initialized = False
            raise

    async def generate_response(
        self,
        prompt: str
    ) -> AsyncGenerator[str, None]:

        if not self.is_initialized:
            await self.initialize()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.temperature,
                max_tokens=1000,
                stream=True
            )

            async for chunk in response:
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(
                f"LLM streaming error: {str(e)}"
            )
            yield f"Error: {str(e)}"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]]
    ) -> str:

        if not self.is_initialized:
            await self.initialize()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.temperature,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(
                f"Chat completion error: {str(e)}"
            )
            return f"Error: {str(e)}"


llm_service = LLMService()