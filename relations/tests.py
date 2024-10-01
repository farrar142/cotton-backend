import time
from base.test import TestCase

from users.models import User, models

from .service import FollowService
from .models import Follow

"""
1. 팔로우 요청[O]
2. 상호 팔로우 체크[O]
3. 팔로우 취소[O]
4. 팔로우 알람
"""


class TestRelation(TestCase):
    user: User
    user2: User
    user3: User

    def test_follower_get_list_order(self):
        service = FollowService(self.user2)
        service.follow(self.user3)
        service = FollowService(self.user)
        service.follow(self.user3)
        service.follow(self.user2)
        self.client.login(self.user)
        resp = self.client.get(f"/relations/{self.user.pk}/followings/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 2)
        self.assertEqual(resp.json()["results"][0]["id"], self.user2.pk)
        self.assertEqual(resp.json()["results"][1]["id"], self.user3.pk)

        self.client.login(self.user3)
        resp = self.client.get(f"/relations/{self.user.pk}/followings/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 2)
        self.assertEqual(resp.json()["results"][0]["id"], self.user2.pk)
        self.assertEqual(resp.json()["results"][0]["is_followed_by"], True)
        self.assertEqual(resp.json()["results"][1]["id"], self.user3.pk)

        resp = self.client.get(f"/relations/{self.user3.pk}/followers/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"].__len__(), 2)
        self.assertEqual(resp.json()["results"][0]["id"], self.user.pk)
        self.assertEqual(resp.json()["results"][0]["is_followed_by"], True)
        self.assertEqual(resp.json()["results"][1]["id"], self.user2.pk)
        self.assertEqual(resp.json()["results"][1]["is_followed_by"], True)

        resp = self.client.get(f"/relations/{self.user3.pk}/followings/")

    def test_is_mutual_following_checkable(self):
        service = FollowService(self.user)
        service.follow(self.user2)
        user2 = (
            User.concrete_queryset(self.user)
            .filter(id=self.user2.pk)
            .get(pk=self.user2.pk)
        )
        self.assertEqual(user2.is_following_to, True)
        self.assertEqual(user2.is_followed_by, False)
        self.assertEqual(user2.is_mutual_follow, False)

        service = FollowService(self.user2)
        service.follow(self.user)
        user2 = (
            User.concrete_queryset(self.user)
            .filter(id=self.user2.pk)
            .get(pk=self.user2.pk)
        )
        self.assertEqual(user2.is_following_to, True)
        self.assertEqual(user2.is_followed_by, True)
        self.assertEqual(user2.is_mutual_follow, True)

    def test_following_2(self):
        s1, s2, s3 = (
            FollowService(self.user),
            FollowService(self.user2),
            FollowService(self.user3),
        )
        s1.follow(self.user3)
        s2.follow(self.user3)

        self.client.login(self.user3)
        resp = self.client.get("/users/me/")
        self.assertEqual(resp.json()["followers_count"], 2)
        print(s3.get_users_followers(self.user3))

    def test_viewsets(self):
        self.client.login(self.user)
        resp = self.client.get("/relations/followings/")
        self.assertEqual(resp.json()["results"].__len__(), 0)
        resp = self.client.post(f"/relations/{self.user3.pk}/follow/")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get("/relations/followings/")
        self.assertEqual(resp.json()["results"].__len__(), 1)
        self.client.login(self.user3)
        resp = self.client.get("/relations/followings/")
        self.assertEqual(resp.json()["results"].__len__(), 0)
        resp = self.client.get("/relations/followers/")
        self.assertEqual(resp.json()["results"].__len__(), 1)
        resp = self.client.get("/relations/mutual_followings/")
        self.assertEqual(resp.json()["results"].__len__(), 0)

        self.client.login(self.user3)
        resp = self.client.post(f"/relations/{self.user.pk}/follow/")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get("/relations/mutual_followings/")
        self.assertEqual(resp.json()["results"].__len__(), 1)

        resp = self.client.delete(f"/relations/{self.user.pk}/follow/")
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get("/relations/mutual_followings/")
        self.assertEqual(resp.json()["results"].__len__(), 0)

    def test_get_profile(self):
        self.client.login(self.user)
        resp = self.client.get(f"/relations/{self.user2.username}/")
        self.assertEqual(resp.status_code, 200)
        print(resp.json())
