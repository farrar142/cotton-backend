import json
from langchain_core.messages import BaseMessage
from langchain_community.chat_models.ollama import ChatOllama
from openai import OpenAI

from django.conf import settings

from base.test import TestCase
from users.models import User
from posts.text_builder.block_text_builder import BlockTextBuilder

from .rag import Rag
from .ai_chat import ai_chat
from .models import ChatBot
from .tasks import is_post_to_chatbot, create_ai_post


class TestAI(TestCase):
    user: User
    user2: User
    user3: User

    def test_rag(self):
        frank = User.objects.create(
            username="frank",
            nickname="frank",
            email="frank@gmail.com",
            password="123456",
        )

        misha = User.objects.create(
            username="misha",
            nickname="misha",
            email="misha@gmail.com",
            password="123456",
        )

        builder = BlockTextBuilder()
        builder.text(f"Hey {misha.nickname}, i'm so tired")

        self.client.login(frank)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)

        content = ai_chat(misha, resp.json())
        builder = BlockTextBuilder()
        builder.text(content or "")

        self.client.login(misha)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                origin=resp.json()["id"],
                parent=resp.json()["id"],
            ),
        )
        self.assertEqual(resp.status_code, 201)
        print(resp.json()["text"])

        prev = self.client.get("/posts/", dict(origin=resp.json()["id"]))

        content = ai_chat(frank, resp.json(), prev.json()["results"])
        builder = BlockTextBuilder()
        builder.text(content or "")

        self.client.login(frank)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)
        print(resp.json()["text"])

    def test_post_to_ai(self):
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
        builder.text("origin")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)
        origin_post_id = resp.json()["id"]
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
        post_id = resp.json()["id"]
        self.assertEqual(bool(is_post_to_chatbot(post_id)), True)
        post = create_ai_post(post_id)
        print(post)
