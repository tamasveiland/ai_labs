"""Conversational agent using Azure OpenAI via Azure AI Foundry.

Maintains conversation history and generates contextual responses
using GPT-4o deployed through Azure AI Foundry.
"""

import logging
from dataclasses import dataclass

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ChatResult:
    """Result of an agent chat call."""

    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

SYSTEM_PROMPT = """\
You are a friendly and helpful voice assistant. You are having a real-time \
voice conversation with a user.

Guidelines:
- Keep responses concise and conversational, typically 1-3 sentences.
- Be natural and engaging, as if chatting with a friend.
- Do not use markdown formatting, bullet points, numbered lists, or special \
characters since your response will be spoken aloud.
- If asked who you are, say you are an AI voice assistant powered by Azure AI.
- Match the user's tone and energy level.
- If unsure about something, be honest and offer to help in a different way.
"""


class ConversationalAgent:
    """Agent that generates responses using Azure OpenAI (GPT-4o)."""

    def __init__(self, config: Config):
        self.config = config
        self.client = self._create_client()
        self.conversation_history: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def _create_client(self) -> AzureOpenAI:
        """Create an Azure OpenAI client with Entra ID authentication."""
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        return AzureOpenAI(
            azure_endpoint=self.config.openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=self.config.openai_api_version,
        )

    def chat(self, user_message: str) -> ChatResult:
        """Send a user message and get an assistant response.

        Args:
            user_message: The transcribed text from the user.

        Returns:
            A ChatResult with the assistant's text and token counts.
        """
        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )

        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_deployment,
                messages=self.conversation_history,
                max_tokens=300,
                temperature=0.7,
            )

            assistant_message = response.choices[0].message.content or ""
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = (
                response.usage.completion_tokens if response.usage else 0
            )

            logger.info(
                "Agent response (%d prompt, %d completion tokens): %s",
                prompt_tokens,
                completion_tokens,
                assistant_message[:100],
            )
            return ChatResult(
                text=assistant_message,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        except Exception as e:
            logger.exception("Agent chat failed")
            # Remove the failed user message to keep history consistent
            self.conversation_history.pop()
            return ChatResult(text=f"I'm sorry, I encountered an error: {e}")

    def reset(self):
        """Reset conversation history for a new conversation."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        logger.info("Conversation history reset")
