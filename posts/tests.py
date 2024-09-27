import base64
from django.conf import settings
from django.db import connection

from base.test import TestCase

from commons.serializers import inject_context
from users.models import User

from .text_builder.block_text_builder import BlockTextBuilder
from .services.post_service import PostService
from .models import Post, Favorite, Bookmark, Repost
from .serializers import (
    PostSerializer,
    FavoriteSerializer,
    BookmarkSerializer,
    RepostSerializer,
    PlainTextSerializer,
)


# 리포스트 된 게시글은 상단으로 올라와야됨 [O]
# 멘션되었을 시 알림을 생성해야됨.
# 좋아요 눌렀을 시 알림을 생성해야됨.


class TestPosts(TestCase):
    user: User

    def test_parser(self):
        builder = BlockTextBuilder()
        builder.text(value="hello")
        self.assertEqual(builder.get_json(), [[dict(type="text", value="hello")]])
        builder.mention(
            id=self.user.pk, username=self.user.username, value=f"@{self.user.username}"
        ).new_line().text("hello")
        ser = PostSerializer(
            data=dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user.pk)],
            ),
            user=self.user,
        )
        self.assertEqual(ser.is_valid(raise_exception=True), True)
        ser.save()
        self.client.login(self.user)
        resp = self.client.get("/posts/timeline/")
        print(resp.json())
        pass

    def test_timeline_reposts_upper(self):
        posts: list[Post] = []
        for i in range(0, 3):
            posts.append(Post(user=self.user, text=f"hello world {i}"))
        posts = Post.objects.bulk_create(posts)
        fp = Post.objects.first()
        if not fp:
            return
        self.client.login(self.user)
        # 리포스트 되지 않은 게시글은 시간순으로 나열됨
        resp = self.client.get("/posts/timeline/followings/")
        self.assertEqual(resp.json()["results"][-1]["id"], fp.pk)

        self.client.login(self.user3)
        resp = self.client.post(f"/posts/{fp.pk}/reposts/")
        self.assertEqual(resp.status_code, 201)

        self.client.login(self.user)
        resp = self.client.post(f"/relations/{self.user3.pk}/follow/")
        self.assertEqual(resp.status_code, 201)
        settings.DEBUG = True
        # 리포스트 된 게시글은 리포스트 된글의 시점에따라 상단으로 올라오도록 함
        resp = self.client.get("/posts/timeline/followings/")
        self.assertEqual(resp.json()["results"][0]["id"], fp.pk)
        self.pprint(resp.json()["results"][0]["relavant_repost"])

    def test_relavant_repost(self):
        self.client.login(self.user)
        builder = BlockTextBuilder()

        self.ps = PostSerializer(
            data=dict(
                text=builder.text("hello world").get_plain_text(),
                blocks=builder.get_json(),
            ),
            user=self.user,
        )
        self.ps.is_valid(raise_exception=True), self.ps.save()
        post_id = self.ps.instance.pk  # type:ignore
        resp = self.client.post(f"/posts/{post_id}/reposts/")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(f"/posts/{post_id}/")
        self.pprint(resp.json())

    def test_image(self):
        with open("./commons/cat.jpg", "rb") as clipped_file:
            clipped_image = clipped_file.read()
        b64_str = base64.b64encode(clipped_image)
        builder = BlockTextBuilder().text(value="hello")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user.pk)],
                images=[dict(url=b64_str.decode())],
            ),
        )
        self.assertEqual(resp.status_code, 201)
        self.pprint(resp.json())


class TestPostsBase(TestCase):
    def setUp(self):
        super().setUp()
        builder = BlockTextBuilder()
        builder.text("hello world")
        self.ps = PostSerializer(
            data=dict(text="hello world", blocks=builder.get_json()), user=self.user
        )
        self.ps.is_valid(raise_exception=True), self.ps.save()

        self.post_id: int = self.ps.instance.pk  # type:ignore


class TestFavorite(TestPostsBase):

    def test_crud_viewsets(self):
        # test unauthorized
        resp = self.client.get(f"/posts/{self.post_id}/favorites/")
        self.client.login(self.user)
        # test get favorites
        resp = self.client.get("/posts/favorites/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 0)
        # test create favorite
        resp = self.client.post(f"/posts/{self.post_id}/favorites/")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(f"/posts/{self.post_id}/favorites/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["is_success"], True)
        # test get favorites
        resp = self.client.get("/posts/favorites/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 1)
        # test mixin
        resp = self.client.get("/posts/bookmarks/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 0)
        # test delete favorite
        resp = self.client.delete(f"/posts/{self.post_id}/favorites/")
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get(f"/posts/{self.post_id}/favorites/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["is_success"], False)


class TestBookmarkSerializer(TestPostsBase):
    def test_create_bookmark(self):
        bs = BookmarkSerializer(data=dict(post=self.post_id), user=self.user)
        bs.is_valid(raise_exception=True)
        bs.save()


class TestRepostSerializer(TestPostsBase):
    def test_create_repost(self):
        rs = RepostSerializer(data=dict(post=self.post_id), user=self.user)
        rs.is_valid(raise_exception=True)
        rs.save()


class TestMention(TestCase):
    def test_mention_created(self):
        self.client.login(self.user)
        builder = BlockTextBuilder()
        builder.text("hello world")
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user2.pk)],
            ),
        )
        self.assertEqual(resp.status_code, 201)


class TestView(TestPostsBase):
    def test_view_create(self):
        self.client.login(self.user)
        resp = self.client.get("/posts/timeline/followings/")
        self.assertEqual(resp.json()["results"][0]["has_view"], False)
        self.assertEqual(resp.json()["results"][0]["views_count"], 0)
        resp = self.client.post(f"/posts/{self.post_id}/views/")
        self.assertEqual(resp.json()["is_success"], True)
        resp = self.client.get("/posts/timeline/followings/")
        self.assertEqual(resp.json()["results"][0]["has_view"], True)
        self.assertEqual(resp.json()["results"][0]["views_count"], 1)
