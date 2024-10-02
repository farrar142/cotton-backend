from base.test import TestCase
from posts.text_builder.block_text_builder import BlockTextBuilder
from .models import Notification, Favorite


class TestNotification(TestCase):
    def test_mentioned_notification(self):
        builder = BlockTextBuilder()
        builder.text("hello").mention(
            value=f"{self.user2.username}",
            id=self.user2.pk,
            username=self.user2.username,
        )
        self.client.login(self.user)
        resp = self.client.post(
            "/posts/", dict(text=builder.get_plain_text(), blocks=builder.get_json())
        )
        self.assertEqual(resp.status_code, 201)
        post_id = resp.json()["id"]
        noti = Notification(
            mentioned_post_id=post_id, user=self.user, from_user=self.user
        )
        noti.save()
        favorite = Favorite.objects.create(post_id=post_id, user=self.user2)
        noti2 = Notification(
            favorited_post=favorite, user=self.user, from_user=self.user2
        )
        noti2.save()

        self.client.login(self.user)
        resp = self.client.post(f"/notifications/{noti2.pk}/check/")
        self.assertEqual(resp.status_code, 201)

        resp = self.client.get("/notifications/")
        self.assertEqual(resp.json()["results"].__len__(), 2)
        self.assertEqual(resp.json()["results"][0]["is_checked"], True)

        self.client.login(self.user2)
        resp = self.client.get("/notifications/")
        self.assertEqual(resp.json()["results"].__len__(), 0)
