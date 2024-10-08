import json
from langchain_core.messages import BaseMessage
from langchain_community.chat_models.ollama import ChatOllama
from openai import OpenAI
from openai.types.chat import ChatCompletionAssistantMessageParam

from django.conf import settings
from users.models import User


def ai_chat(ai: User, post: dict, previous_post: list[dict] | None = None) -> str:
    assistant = ChatCompletionAssistantMessageParam(role="assistant", content="")
    if previous_post:
        assistant = ChatCompletionAssistantMessageParam(
            role="assistant", content=json.dumps(previous_post)
        )
    ollama = OpenAI(base_url=settings.OLLAMA_URL, api_key="ollama")
    result = ollama.chat.completions.create(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": f"Your name is {ai.nickname}, you have to reply to user's sns post",
            },
            {
                "role": "system",
                "content": " If you don't know the answer, just say that you don't know, don't try to make up an answer",
            },
            {
                "role": "system",
                "content": "It’s okay to omit the other users’s nickname.",
            },
            assistant,
            {"role": "user", "content": json.dumps(post)},
        ],
        max_tokens=2048 * 4,
        max_completion_tokens=100,
    )
    return result.choices[0].message.content or ""
