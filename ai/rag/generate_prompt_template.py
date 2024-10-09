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


def generate_prompt_template():
    prompt_template = """
    You have to make sns post, within the context given below.
    
    Just give me a post, without additional explanation

    If you don't know the answer, don't try to answer, just say you don't know.

    you can use only under 200 characters.
    
    Hide you are an AI.
    
    {context}

    question: {question}
    kindly answer:"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    system_template = """
    You have to make sns post, within the context given below.
    
    Just give me a post, without additional explanation

    If you don't know the answer, don't try to answer, just say you don't know.
    
    you can use only under 200 characters.
    
    Hide you are an AI.
    ----------------
    {context}"""

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
    CHAT_PROMPT = ChatPromptTemplate.from_messages(messages)

    PROMPT_SELECTOR = ConditionalPromptSelector(
        default_prompt=PROMPT, conditionals=[(is_chat_model, CHAT_PROMPT)]
    )
    return PROMPT_SELECTOR


def generate_reply_prompt_template(user: "User"):
    user_define_prompt = f"Your name is {user.nickname}.\n"
    prompt_template = (
        user_define_prompt
        + """
    
    You have to reply to user's sns post, within the context given below.

    If you don't know the answer, don't try to answer, just say you don't know.

    you can use only under 200 characters.
    
    Hide you are an AI.
    {context}

    question: {question}
    reply:"""
    )
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    system_template = (
        user_define_prompt
        + """
    You have to reply to user's sns post, within the context given below.

    If you don't know the answer, don't try to answer, just say you don't know.

    you can use only under 200 characters.
    
    Hide you are an AI.
    ----------------
    {context}"""
    )

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
    CHAT_PROMPT = ChatPromptTemplate.from_messages(messages)

    PROMPT_SELECTOR = ConditionalPromptSelector(
        default_prompt=PROMPT, conditionals=[(is_chat_model, CHAT_PROMPT)]
    )
    return PROMPT_SELECTOR
