import hashlib
from random import shuffle
import chromadb, os, bs4
from langchain_core.documents import Document
from langchain_community.document_loaders import CSVLoader, TextLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models.ollama import ChatOllama
import requests

from .generate_prompt_template import generate_prompt_template


def get_hash(string: str):
    return hashlib.md5(string.encode()).hexdigest()


def split_docs(documents: list[Document], chunk_size=1000, chunk_overlap=1000):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(documents)


def get_news_urls(
    origin="https://news.naver.com/",
    icontain: str = "/article/",
):
    response = requests.get(origin)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
    results = soup.select("a")
    urls = list(
        set(
            filter(
                lambda x: icontain in x,
                map(lambda x: str(x.get("href", "")), results),
            )
        )
    )
    shuffle(urls)
    return urls


def filter_existing_urls(urls: list[str], collection_name: str):
    # 1. 존재하는 document의  metadata들을 가져옴
    collection = chroma.get_or_create_collection(collection_name)
    results = collection.get(where={"source": {"$in": urls}})  # type:ignore
    # 2. 필터
    existing_source = [
        metadata.get("source") for metadata in (results.get("metadatas") or [])
    ]
    return list(set(urls).difference(existing_source))


def get_documents_from_urls(
    urls: list[str], limit: int = 10, tag: str = "article", id: str = "dic_area"
):

    loader = WebBaseLoader(
        web_paths=urls[:limit],
        bs_kwargs=dict(parse_only=bs4.SoupStrainer(tag, {"id": id})),
    )
    return loader.load()


chatollama = ChatOllama(
    model="llama3",
)
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

    def _get_chroma(self, collection_name: str):

        db = Chroma(
            collection_name, client=self.chroma, embedding_function=self.embedding
        )
        return db

    def save_news_to_db(self, documents: list[Document], collection_name: str = "news"):
        self.__save_documents_by_embbeding(documents, collection_name)

    def truncate_collection(self, collection_name: str):
        self.chroma.get_or_create_collection(collection_name)
        self.chroma.delete_collection(collection_name)

    def ask_llm(
        self, query: str, db: Chroma | None = None, collection_name: str = "news"
    ):
        if not db:
            db = self._get_chroma(collection_name=collection_name)
        from langchain.chains.question_answering import load_qa_chain

        prompt = generate_prompt_template().get_prompt(self.client)
        chain = load_qa_chain(
            self.client,
            chain_type="stuff",
            verbose=False,
            prompt=prompt,
        )
        matching_docs = db.similarity_search(query=query)
        return chain.run(input_documents=matching_docs, question=query)
