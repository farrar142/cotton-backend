from openai import OpenAI
import hashlib
import chromadb, os, redis, bs4
from langchain_core.documents import Document
from langchain_community.document_loaders import CSVLoader, TextLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
    OpenAIEmbeddings,
)
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models.ollama import ChatOllama
from langchain.prompts import (
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
    BasePromptTemplate,
    PromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains.prompt_selector import ConditionalPromptSelector, is_chat_model
import redis.client
import requests

from django.conf import settings


prompt_template = """아래에 주어진 컨텍스트 내에서, 질문에 대해 한국어로 친절하게 답해줘.

만약에 답을 모르겠으면,답을 하려하지 말고 그냥 모른다고 답해줘. 

{context}

질문: {question}
친절한 대답:"""
PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

system_template = """아래에 주어진 컨텍스트 내에서, 질문에 대해 한국어로 친절하게 답해줘.

만약에 답을 모르겠으면,답을 하려하지 말고 그냥 모른다고 답해줘. 
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


def get_hash(string: str):
    return hashlib.md5(string.encode()).hexdigest()


def split_docs(documents: list[Document], chunk_size=1000, chunk_overlap=1000):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(documents)


def get_news_urls(origin="https://news.naver.com/"):
    response = requests.get(origin)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
    results = soup.select("a")
    return list(
        set(
            filter(
                lambda x: "/article/" in x,
                map(lambda x: str(x.get("href", "")), results),
            )
        )
    )


def get_documents_from_urls(urls: list[str], limit: int = 10):

    loader = WebBaseLoader(
        web_paths=urls[:10],
        bs_kwargs=dict(parse_only=bs4.SoupStrainer("article", {"id": "dic_area"})),
    )
    return loader.load()


class Rag:
    def __init__(self):
        self.client = ChatOllama(
            model="llama3",
        )
        self.client.base_url = "http://host.docker.internal:11434"
        self.chroma = chromadb.HttpClient(host="192.168.0.14", port=10000)
        self.embedding = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-l6-v2", model_kwargs=dict(device="cuda")
        )

    def __save_documents_by_embbeding(
        self, documents: list[Document], collection_name: str
    ) -> Chroma:
        db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding,
            client=self.chroma,
            collection_name=collection_name,
        )
        return db

    def __get_chroma(self, collection_name: str):

        db = Chroma(
            collection_name, client=self.chroma, embedding_function=self.embedding
        )
        return db

    def save_news_to_db(self, collection_name: str = "news"):
        urls = get_news_urls()
        documents = get_documents_from_urls(urls)
        self.__save_documents_by_embbeding(documents, collection_name)

    def ask_llm(
        self, query: str, db: Chroma | None = None, collection_name: str = "news"
    ):
        if not db:
            db = self.__get_chroma(collection_name=collection_name)
        from langchain.chains.question_answering import load_qa_chain

        chain = load_qa_chain(
            self.client,
            chain_type="stuff",
            verbose=True,
            prompt=PROMPT_SELECTOR.get_prompt(self.client),
        )
        matching_docs = db.similarity_search(query=query)
        return chain.run(input_documents=matching_docs, question=query)
