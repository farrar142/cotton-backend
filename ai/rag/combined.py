from django.utils.timezone import localtime


def _crawl_huffinton_post(collection_name: str = "huffington"):
    from . import get_documents_from_urls, get_news_urls, filter_existing_urls, Rag

    urls = get_news_urls("https://huffpost.com", icontain="/entry/")
    filtered_urls = filter_existing_urls(urls, collection_name)
    if not filtered_urls:
        return
    docs = get_documents_from_urls(filtered_urls, 10, tag="main", id="main")
    now = localtime().isoformat()
    for doc in docs:
        doc.metadata.setdefault("created_at", now)
    rag = Rag()
    rag.save_news_to_db(docs, collection_name)
