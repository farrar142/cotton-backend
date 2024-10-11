from random import shuffle
from typing import TYPE_CHECKING
import chromadb, os, bs4
from langchain_core.documents import Document
from langchain_community.document_loaders import CSVLoader, TextLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
)

from langchain_chroma import Chroma

# from langchain_community.vectorstores import Chroma
from langchain_community.chat_models.ollama import ChatOllama
import requests

from .generate_prompt_template import (
    generate_prompt_template,
    generate_reply_prompt_template,
)
from .loader import PostLoader
import torch

if TYPE_CHECKING:
    from users.models import User
    from posts.models import Post

torch.multiprocessing.set_start_method("spawn")


def get_documents_from_posts(posts: "list[Post]", user: "User"):
    loader = PostLoader(posts=posts, user=user)
    return loader.load()


chatollama = ChatOllama(model="lumimaid", timeout=100)
chatollama.base_url = os.getenv("OLLAMA_URL", "")
chroma = chromadb.HttpClient(host="192.168.0.14", port=10000)
embedding = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-l6-v2", model_kwargs=dict(device="cuda")
)


class Rag:
    def __init__(self):
        self.client = chatollama
        self.chroma = chroma
        self.embedding = embedding

    def _get_chroma(self, collection_name: str):

        db = Chroma(
            collection_name, client=self.chroma, embedding_function=self.embedding
        )
        return db

    def save_documents_by_embbeding(
        self, documents: list[Document], collection_name: str
    ) -> Chroma:
        db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding,
            client=self.chroma,
            collection_name=collection_name,
        )
        return db

    def truncate_collection(self, collection_name: str):
        self.chroma.get_or_create_collection(collection_name)
        self.chroma.delete_collection(collection_name)

    def ask_llm(
        self,
        chatbot: "User",
        query: str,
        db: Chroma | None = None,
        collection_name: str = "news",
    ) -> str:
        from langchain.chains.question_answering import load_qa_chain

        if not db:
            db = self._get_chroma(collection_name=collection_name)

        ""
        prompt = generate_prompt_template(chatbot).get_prompt(self.client)
        chain = load_qa_chain(
            self.client,
            chain_type="stuff",
            verbose=False,
            prompt=prompt,
        )
        matching_docs = db.similarity_search(query=query)

        result = chain.invoke(
            input=dict(input_documents=matching_docs, question=query),
        )
        return result["output_text"]

    def create_reply(
        self,
        chatbot: "User",
        user: "User",
        query: str,
        post_docs: list[Document],
        collection_name: str = "huffington",
    ) -> str:
        from langchain.chains.question_answering import load_qa_chain

        db = self._get_chroma(collection_name=collection_name)
        prompt = generate_reply_prompt_template(chatbot, user).get_prompt(self.client)
        chain = load_qa_chain(
            self.client, chain_type="stuff", verbose=False, prompt=prompt
        )
        matching_docs = db.similarity_search(query=query)
        # chain.invoke()
        result = chain.invoke(
            input=dict(input_documents=[*matching_docs, *post_docs], question=query),
        )
        return result["output_text"]
