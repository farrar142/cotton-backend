from typing import TYPE_CHECKING
from langchain.prompts import (
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
    PromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.chains.prompt_selector import ConditionalPromptSelector, is_chat_model

if TYPE_CHECKING:
    from users.models import User


def chatbot_define_prompt(chatbot: "User", user: "User|None" = None):
    name_prompt = f"Your name is {chatbot.nickname}.\n"
    if not chatbot.chat_bots or not chatbot.chat_bots.character:
        return name_prompt

    user_nickname = user.nickname if user else "user"

    character_prompt = chatbot.chat_bots.character.format(
        chatbot=chatbot.nickname, user=user_nickname
    )

    return name_prompt + character_prompt


def user_define_prompt(user: "User"):
    return f"Now you are talking with {user.nickname}"


def generic_prompt(chatbot: "User", user: "User|None" = None):
    return (
        chatbot_define_prompt(chatbot, user)
        + "If you don't know the answer, don't try to answer, just say you don't know.\nyou can use only under 200 characters.\nHide you are an AI.\n"
    )


def generate_prompt_template(user: "User"):
    def get_default_prompt():
        prompt_template = (
            generic_prompt(user)
            + """----------------
        {context}

        question: {question}
        kindly answer:"""
        )
        return PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

    def get_chat_prompt():
        system_template = (
            generic_prompt(user)
            + """----------------
        {context}"""
        )

        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]
        return ChatPromptTemplate.from_messages(messages)

    PROMPT_SELECTOR = ConditionalPromptSelector(
        default_prompt=get_default_prompt(),
        conditionals=[(is_chat_model, get_chat_prompt())],
    )
    return PROMPT_SELECTOR


def generate_reply_prompt_template(chatbot: "User", user: "User"):
    def get_default_prompt():
        prompt_template = (
            generic_prompt(chatbot, user)
            + user_define_prompt(user)
            + """---------------
        {context}

        question: {question}
        reply:"""
        )
        return PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

    def get_chat_prompt():
        system_template = (
            generic_prompt(chatbot)
            + user_define_prompt(user)
            + """----------------
        {context}"""
        )

        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]
        return ChatPromptTemplate.from_messages(messages)

    PROMPT_SELECTOR = ConditionalPromptSelector(
        default_prompt=get_default_prompt(),
        conditionals=[(is_chat_model, get_chat_prompt())],
    )
    return PROMPT_SELECTOR
