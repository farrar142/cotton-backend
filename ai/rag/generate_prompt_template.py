from langchain.prompts import (
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
    PromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.chains.prompt_selector import ConditionalPromptSelector, is_chat_model


def generate_prompt_template():
    prompt_template = """Please kindly answer my questions, within the context given below.

    If you don't know the answer, don't try to answer, just say you don't know.

    {context}

    question: {question}
    kindly answer:"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    system_template = """Please kindly answer my questions, within the context given below.

    If you don't know the answer, don't try to answer, just say you don't know.
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
