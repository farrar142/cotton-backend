import bs4
import requests
from random import shuffle
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.api import ClientAPI as ChromaClientAPI


def split_docs(documents: list[Document], chunk_size=1000, chunk_overlap=1000):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(documents)


def get_documents_from_urls_v2(urls: list[str], tag: str, attrs: dict, limit: int = 10):

    loader = WebBaseLoader(
        web_paths=urls[:limit],
        bs_kwargs=dict(parse_only=bs4.SoupStrainer(tag, attrs)),
    )
    return loader.load()


def get_documents_from_urls(
    urls: list[str], limit: int = 10, tag: str = "article", id: str = "dic_area"
):

    loader = WebBaseLoader(
        web_paths=urls[:limit],
        bs_kwargs=dict(parse_only=bs4.SoupStrainer(tag, {"id": id})),
    )
    return loader.load()


def filter_existing_urls(
    urls: list[str], collection_name: str, chroma: ChromaClientAPI
):
    # 1. 존재하는 document의  metadata들을 가져옴
    collection = chroma.get_or_create_collection(collection_name)
    results = collection.get(where={"source": {"$in": urls}})  # type:ignore
    # 2. 필터
    existing_source = [
        metadata.get("source") for metadata in (results.get("metadatas") or [])
    ]
    return list(set(urls).difference(existing_source))


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
    empty_filtered = list(filter(lambda x: x != "", urls))
    shuffle(empty_filtered)
    return empty_filtered
