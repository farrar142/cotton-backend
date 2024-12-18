import base64
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import localtime

from base.test import TestCase
from commons.caches import LRUCache, TimeoutCache

from users.models import User

from .services.recommend_service import RecommendService
from .text_builder.block_text_builder import BlockTextBuilder
from relations.service import FollowService
from .models import Post, Favorite, Bookmark, Repost, View, models
from .serializers import (
    PostSerializer,
    FavoriteSerializer,
    BookmarkSerializer,
    RepostSerializer,
    PlainTextSerializer,
)
from .documents import PostDocument as PD


# 리포스트 된 게시글은 상단으로 올라와야됨 [O]
# 멘션되었을 시 알림을 생성해야됨.
# 좋아요 눌렀을 시 알림을 생성해야됨.


class TestPostPagination(TestCase):
    def test_pagination(self):
        Post.objects.all().delete()
        resp = self.client.get(f"/posts/timeline/username/{self.user.username}/")
        self.assertEqual(resp.status_code, 200)
        self.pprint(resp.json())
        posts = Post.objects.bulk_create(
            [Post(text=str(i), user=self.user) for i in range(5)], batch_size=1
        )
        self.client.login(self.user)
        resp = self.client.get(f"/posts/timeline/username/{self.user.username}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"][0]["id"], posts[-1].pk)
        current_offset = resp.json()["current_offset"]
        offset_field = resp.json()["offset_field"]
        new_posts = Post.objects.bulk_create(
            [Post(text=str(i), user=self.user) for i in range(3)], batch_size=1
        )
        resp = self.client.get(
            f"/posts/timeline/username/{self.user.username}/",
            dict(offset=current_offset),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"][0]["id"], posts[-1].pk)

        resp = self.client.get(
            f"/posts/timeline/username/{self.user.username}/",
            dict(offset=current_offset, direction="prev"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 3)
        self.assertEqual(resp.json()["results"][0]["id"], new_posts[-1].pk)


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
        pass

    def test_timeline_reposts_upper(self):
        Post.objects.all().delete()
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

        resp = self.client.get(f"/posts/timeline/username/{self.user.username}/media/")
        self.assertEqual(resp.status_code, 200)

    def test_replies(self):
        builder = BlockTextBuilder().text(value="hello")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user.pk)],
            ),
        )
        self.assertEqual(resp.status_code, 201)
        post_id = resp.json()["id"]

        resp = self.client.get(
            f"/posts/timeline/username/{self.user.username}/replies/"
        )
        self.assertEqual(resp.json()["results"].__len__(), 0)

        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                parent=post_id,
                origin=post_id,
            ),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["parent"], post_id)
        self.assertEqual(resp.json()["origin"], post_id)
        self.assertEqual(resp.json()["depth"], 1)
        post2_id = resp.json()["id"]

        resp = self.client.get(f"/posts/{post_id}/")
        self.assertEqual(resp.json().get("replies_count"), 1)

        resp = self.client.get(
            f"/posts/timeline/username/{self.user.username}/replies/"
        )
        self.assertEqual(resp.json()["results"].__len__(), 1)
        self.client.login(self.user2)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                parent=post2_id,
                origin=post_id,
            ),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["parent"], post2_id)
        self.assertEqual(resp.json()["origin"], post_id)
        self.assertEqual(resp.json()["depth"], 2)
        post3_id = resp.json()["id"]

        resp = self.client.get(
            f"/posts/timeline/username/{self.user2.username}/replies/"
        )
        self.assertEqual(resp.json()["results"].__len__(), 1)
        self.assertEqual(resp.json()["results"][0]["depth"], 2)
        self.assertEqual(resp.json()["results"][0]["origin"], post_id)
        self.assertEqual(resp.json()["results"][0]["id"], post3_id)

        resp = self.client.get(f"/posts/{post_id}/")
        self.assertEqual(resp.json()["replies_count"], 1)

        resp = self.client.get(f"/posts/{post2_id}/")
        self.assertEqual(resp.json()["replies_count"], 1)
        resp = self.client.get(f"/posts/{post_id}/replies/")
        self.assertEqual(resp.status_code, 200)

    def test_quote(self):
        builder = BlockTextBuilder().text(value="hello")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user.pk)],
            ),
        )
        self.assertEqual(resp.status_code, 201)
        post_id = resp.json()["id"]

        resp = self.client.post(
            "/posts/",
            dict(
                text=builder.get_plain_text(),
                blocks=builder.get_json(),
                mentions=[dict(mentioned_to=self.user.pk)],
                quote=post_id,
            ),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json().get("quote"), post_id)

        resp = self.client.get(f"/posts/{post_id}/")
        self.assertEqual(resp.json().get("quotes_count"), 1)
        self.assertEqual(resp.json().get("has_quote"), True)


class TestPostsBase(TestCase):
    user: User
    user2: User
    user3: User

    def create_post(self, user: User, **kwargs) -> int:
        builder = BlockTextBuilder()
        builder.text("hello world")
        self.ps = PostSerializer(
            data=dict(text="hello world", blocks=builder.get_json(), **kwargs),
            user=user,
        )
        self.ps.is_valid(raise_exception=True), self.ps.save()
        return self.ps.instance.pk  # type:ignore

    def setUp(self):
        super().setUp()
        Post.objects.all().delete()

        self.post_id: int = self.create_post(self.user)


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


class TestProtected(TestPostsBase):
    def test_cannot_see_protected_users(self):
        post2_id = self.create_post(self.user2)
        self.user.is_protected = True
        self.user.save()
        self.client.login(self.user)
        resp = self.client.get(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(f"/posts/")
        self.assertEqual(resp.json()["results"].__len__(), 2)

        self.client.login(self.user2)
        resp = self.client.get(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 404)

        FollowService(self.user).follow(self.user2)
        FollowService(self.user2).follow(self.user)

        self.client.login(self.user2)
        resp = self.client.get(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(f"/posts/timeline/global/")
        self.assertEqual(resp.json()["results"].__len__(), 2)
        resp = self.client.get(f"/posts/timeline/followings/")
        self.assertEqual(resp.json()["results"].__len__(), 2)
        resp = self.client.get(f"/posts/timeline/username/{self.user.username}/")
        self.assertEqual(resp.json()["results"].__len__(), 1)

        self.client.login(self.user3)
        resp = self.client.get(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get(f"/posts/timeline/global/")
        self.assertEqual(resp.json()["results"].__len__(), 1)
        resp = self.client.get(f"/posts/timeline/username/{self.user.username}/")
        self.assertEqual(resp.json()["results"].__len__(), 0)


class TestDeletedPost(TestPostsBase):
    def test_delete_post(self):
        self.client.login(self.user2)
        resp = self.client.delete(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 403)

        self.client.login(self.user)
        resp = self.client.delete(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 204)

    def test_handle_origin_when_deleted(self):
        from django.db import models

        post_2 = self.create_post(self.user2, origin=self.post_id, parent=self.post_id)
        post_3 = self.create_post(self.user3, origin=self.post_id, parent=post_2)
        self.client.login(self.user)
        resp = self.client.delete(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get(f"/posts/{self.post_id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["text"], "")

        resp = self.client.get(f"/posts/flat/")
        self.assertEqual(resp.json().__len__(), 2)


class TestRecommended(TestPostsBase):
    def test_recommend(self):
        with LRUCache("test", 1) as cache:
            cache.trunc()
            cache.add(*range(10))
            self.assertEqual(len(cache.all()), 1)
            self.assertEqual(cache.all(), [9])

        with LRUCache("test", 20) as cache:
            cache.trunc()
            cache.add(*range(10))
            cache.add(*range(5))
        from django.utils.timezone import localtime

        with TimeoutCache("post_recommended") as cache:
            cache.trunc()
            cache.add(1, 2, 3, 4, 5)
            cache.remove_out_dated(localtime() + timedelta(minutes=10))
            self.assertEqual(cache.all(), [])

        with TimeoutCache("post_recommended") as cache:
            cache.trunc()
            cache.add(1, 2, 3, 4, 5)
            cache.remove_out_dated(localtime() - timedelta(minutes=10))
            self.assertEqual(cache.all().__len__(), 5)

        with TimeoutCache("post_recommended") as cache:
            cache.trunc()
            cache.add(1, 2, 3, 4, 5)
            cache.add(1)
            print(cache.all())
            counter = cache.counter()
            self.assertEqual(counter[0], 1)

    def test_recommended_order(self):
        post_2 = self.create_post(self.user2)
        posts = [Post(user=self.user, text=f"{i}") for i in range(100)]
        posts = Post.objects.bulk_create(posts)
        cache.delete(f"cached_sessions/v2:{self.user.pk}")
        with TimeoutCache("post_recommended/v2") as tc:
            tc.trunc()
            tc.add(self.post_id, weights=2)
            tc.add(post_2)
            tc.add(*map(lambda x: x.pk, posts), weights=1)

            counter = tc.counter()
            self.assertEqual(counter[0], self.post_id)
        self.client.login(self.user)
        resp = self.client.get("/posts/timeline/global/", dict(session_min_size=0))
        self.assertEqual(resp.json()["results"][0]["id"], self.post_id)
        cp = resp.json()["current_offset"]
        resp = self.client.get(
            "/posts/timeline/global/", dict(offset=cp, direction="prev")
        )
        self.pprint(resp.json())

    def test_exceed_cache(self):
        print("run")
        from django.utils.timezone import localtime

        Post.objects.all().delete()
        post_2 = self.create_post(self.user2)
        posts = [Post(user=self.user, text=f"{i}") for i in range(100)]
        posts = Post.objects.bulk_create(posts)
        print("post create")
        cache.delete(f"cached_sessions/v2:{self.user.pk}")
        with TimeoutCache("post_recommended/v2") as tc:
            tc.trunc()
            tc.add(self.post_id, weights=2, created_at=localtime() - timedelta(hours=1))
            tc.add(post_2, created_at=localtime() - timedelta(hours=1))
            tc.add(
                *map(lambda x: x.pk, posts),
                weights=1,
                created_at=localtime() - timedelta(hours=1),
            )

            counter = tc.counter()
            self.assertEqual(counter[0], self.post_id)
            tc.remove_out_dated(localtime())
            self.assertEqual(tc.counter().__len__(), 100)
            tc.remove_out_dated(localtime(), 150)
            self.assertEqual(tc.counter().__len__(), 100)


class TestElasticSearch(TestCase):
    def test_es(self):
        resp = self.client.get("/posts/timeline/search/", dict(search="#TeslaStock"))
        self.assertEqual(resp.status_code, 200)

    def test_recommended_vector(self):
        user = User.objects.get(username="Sandring")
        favorite_post = models.Q(favorites__user=user)
        repost_post = models.Q(reposts__user=user)

        posts = Post.objects.filter(favorite_post | repost_post).order_by(
            "-created_at"
        )[:10]
        self.assertEqual(posts.exists(), True)
        service = RecommendService
        near = service.get_post_knn(posts)
        near = service.get_user_knn(posts)

    def test_tokenizer(self):
        resp = self.client.get("/posts/timeline/recommended/tags/")
        self.pprint(resp.json())

    def test_recommend_user(self):
        user = User.objects.filter(username="Sandring").first()
        self.client.login(user)
        resp = self.client.get("/relations/users/recommended/")
        self.pprint(resp.json())


class TestHashtag(TestCase):
    def test_hash_tag(self):
        builder = BlockTextBuilder()
        builder.text("awd dawdd #asdf adwdawdaw").new_line().text("ffff #ddawdas ")
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)
