import json
from langchain_core.messages import BaseMessage
from langchain_community.chat_models.ollama import ChatOllama
from openai import OpenAI

from django.conf import settings
from django.utils.timezone import localtime

from base.test import TestCase
from users.models import User
from posts.text_builder.block_text_builder import BlockTextBuilder
from posts.models import Post

from .rag import Rag, get_documents_from_urls, get_news_urls, filter_existing_urls
from .ai_chat import ai_chat
from .models import ChatBot
from .tasks import is_post_to_chatbot, create_ai_post

"""

  1. 유저와의 대화기록을 벡터db에 저장.
  2. 대화기록 벡터 db에서 유저의 게시글로 search후 document를 반환
  3. 뉴스 벡터 db에서 유저의 게시글로 연관 documents를 반환
"""


class TestAI(TestCase):
    user: User
    user2: User
    user3: User

    def test_is_post_to_ai(self):
        cb = ChatBot.objects.create(user=self.user)
        builder = BlockTextBuilder()
        builder.text("origin")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)
        origin_post_id = resp.json()["id"]
        # 본인이 쓴건 false여야됨
        self.assertEqual(bool(is_post_to_chatbot(origin_post_id)), False)

        self.client.login(self.user2)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                parent=origin_post_id,
            ),
        )
        self.assertEqual(resp.status_code, 201)
        post_id = resp.json()["id"]
        # 답글 달린건 True여야됨
        self.assertEqual(bool(is_post_to_chatbot(post_id)), True)

        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                quote=origin_post_id,
            ),
        )
        self.assertEqual(resp.json()["quote"], origin_post_id)
        # 인용 된것도 True여야됨
        post_id = resp.json()["id"]
        self.assertEqual(bool(is_post_to_chatbot(post_id)), True)
        builder.mention(
            id=self.user.pk, username=self.user.username, value=self.user.nickname
        )
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user.pk)],
            ),
        )
        # 멘션 된것도 True여야됨
        post_id = resp.json()["id"]
        self.assertEqual(bool(is_post_to_chatbot(post_id)), True)

    def test_post_to_ai_and_reply(self):

        cb = ChatBot.objects.create(user=self.user)
        builder = BlockTextBuilder()
        builder.text("what do you think about NASA's new Spaceship?")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)
        origin_post_id = resp.json()["id"]
        self.assertEqual(bool(is_post_to_chatbot(origin_post_id)), False)

        self.client.login(self.user)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                parent=origin_post_id,
                origin=origin_post_id,
            ),
        )
        post_id = resp.json()["id"]
        self.assertEqual(bool(is_post_to_chatbot(post_id)), True)
        create_ai_post(post_id)
        p = Post.objects.last()
        create_ai_post(p.pk)

    def test_celery_queue(self):
        rag = Rag()
        """
        1. 외부 site에서 뉴스를 크롤링해 저장해야됨.
        2. 컬렉션에 덮어쓰기 하면안됨
        3. 중복된 소스들은 저장하지 말아야됨
        """
        collection_name = "huff-test"
        d_urls = [
            "https://www.huffpost.com/entry/scott-perry-project-2025_n_670416f6e4b0f65b8775e550",
            "https://www.huffpost.com/entry/trisha-yearwood-garth-brooks-alleged-assault_n_67059ec1e4b09945d6b87df6",
            "https://www.huffpost.com/entry/last-dog-downsizing-retirement-family_n_66e5e834e4b0e9e4c582ba25",
            "https://www.huffpost.com/entry/prime-day-cleaning-deals-2024_l_66fdec71e4b09a8f8487a938",
            "https://www.huffpost.com/entry/affordable-buys-prime-day-2024_l_66eb02f1e4b051614c50b95c",
            "https://www.huffpost.com/entry/prime-day-cleaning-deals-2024-sc_l_6704414fe4b0924ce9db1fab",
            "https://www.huffpost.com/entry/sum-41-deryck-whibley-sexual-abuse-allegations_n_67056abee4b09585e726e3b6",
            "https://www.huffpost.com/entry/hotel-bathtubs-germs_l_66688840e4b01bc0ceed892e",
            "https://www.huffpost.com/entry/billie-eilish-never-talking-sexuality_n_670573fbe4b09945d6b864e8",
            "https://www.huffpost.com/entry/lisa-marie-presley-dead-son-on-ice_n_670540ace4b00a4f9829b0e4",
            "https://www.huffpost.com/entry/frugal-deals-october-prime-day-2024_l_66faf561e4b06bc72dbbf228",
        ]
        collection = rag.chroma.get_or_create_collection(collection_name)
        results = collection.get()
        rag.chroma.delete_collection(collection_name)

        def save():
            # urls = get_news_urls("https://huffpost.com", icontain="/entry/")
            urls = filter_existing_urls(d_urls, collection_name)
            docs = get_documents_from_urls(urls, 10, tag="main", id="main")
            for doc in docs:
                doc.metadata.setdefault("created_at", localtime().isoformat())
            rag.save_news_to_db(docs, collection_name)

        save()

        collection = rag.chroma.get_or_create_collection(collection_name)
        results = collection.get()
        docs = results.get("documents")
        if not docs:
            self.assertEqual(True, False)
            return
        self.assertEqual(docs.__len__(), 10)

        save()

        results = collection.get()
        docs = results.get("documents")
        if not docs:
            self.assertEqual(True, False)
            return
        self.assertEqual(docs.__len__(), 11)

    def test_ai_tweet_auto(self):
        collection_name = "huff-test"
        rag = Rag()
        rag.truncate_collection(collection_name)
        from posts.serializers import PostSerializer
        from .rag.combined import _crawl_huffinton_post

        _crawl_huffinton_post(collection_name)

        resp: str = rag.ask_llm(
            "Please summarize just random one of today's news and make it like an sns post to your followers. \n Leave out the additional explanation and hashtags.\nWrite down your thoughts naturally too",
            collection_name=collection_name,
        )

        builder = BlockTextBuilder()
        splitted = resp.split("\n")
        for text in splitted:
            builder.text(text)
        ser = PostSerializer(
            data=dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
            ),
            user=self.user,
        )
        if not ser.is_valid():
            return
        ser.save()
        print(ser.instance)

    def test_is_chatbot(self):
        ChatBot.objects.create(user=self.user)
        users = User.objects.filter(chatbots__isnull=False)
        self.assertEqual(users.count(), 1)
