from django.db import connection, transaction
from base.test import TestCase
from commons.lock import with_lock

from relations.service import FollowService

from .models import MessageGroup, MessageAttendant, Message, User, models
from .serializers import MessageGroupSerializer
from .services import MessageService


class TestMessages(TestCase):
    user: User
    user2: User
    user3: User

    def test_main(self):
        service = MessageService.create(self.user, self.user2)
        self.assertEqual(self.user.message_attendants.count(), 1)
        self.assertEqual(self.user.message_groups.count(), 1)
        # user1 create message
        service.send_message(self.user, "hello user2")
        service.send_message(self.user2, "hello user1")

        messages = Message.objects.filter(attendant__group=service.group)
        self.assertEqual(messages.count(), 2)

    def test_find_direct_message(self):
        service = MessageService.create(self.user, self.user2, is_direct_message=False)
        self.assertEqual(self.user.message_attendants.count(), 1)
        self.assertEqual(self.user.message_groups.count(), 1)

        service = MessageService.create(self.user, self.user2)
        self.assertEqual(self.user.message_attendants.count(), 2)
        self.assertEqual(self.user.message_groups.count(), 2)

        service = MessageService.create(self.user, self.user3)
        self.assertEqual(self.user.message_attendants.count(), 3)
        self.assertEqual(self.user.message_groups.count(), 3)

        last_queries = connection.queries.__len__()
        dm = MessageService.get_direct_message_group(self.user, self.user2)
        print(dm)

        current_queries = connection.queries.__len__()
        self.assertEqual(current_queries - last_queries, 2)

        groups = MessageService.get_message_groups(self.user)
        self.assertEqual(groups.count(), 3)

    def test_viewset(self):
        self.client.login(self.user)
        # 그룹메세지 만들기
        resp = self.client.post(
            "/message_groups/create/", dict(users=[self.user.pk, self.user2.pk])
        )
        self.assertEqual(resp.status_code, 201)
        s1 = MessageService(MessageGroup.objects.get(pk=resp.json()["id"]))

        resp = self.client.post(
            "/message_groups/create/", dict(users=[self.user.pk, self.user3.pk])
        )
        self.assertEqual(resp.status_code, 201)
        s2 = MessageService(MessageGroup.objects.get(pk=resp.json()["id"]))

        # 그룹가져오기
        resp = self.client.get("/message_groups/")
        self.assertEqual(resp.json()["results"].__len__(), 2)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"][0]["id"], s2.group.pk)

        # 그룹메세지 보내기
        self.client.post(
            f"/message_groups/{s2.group.pk}/send_message/", dict(message="1")
        )
        self.client.login(self.user3)
        self.client.post(
            f"/message_groups/{s2.group.pk}/send_message/", dict(message="2")
        )
        # s2.send_message(self.user, "1")
        # s2.send_message(self.user3, "2")

        resp = self.record_query(self.client.get)("/message_groups/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["results"][0]["id"], s2.group.pk)
        self.assertEqual(resp.json()["results"][0]["latest_message"], "2")

        resp = self.client.get(f"/message_groups/{s2.group.pk}/messages/")
        self.assertEqual(resp.status_code, 200)
        # self.pprint(resp.json())

    def test_multi_group(self):
        self.client.login(self.user)
        resp = self.client.get("/users/", dict(id__isnot=self.user.pk))
        self.assertEqual(resp.status_code, 200)
        # 그룹메세지 만들기
        resp = self.client.post(
            "/message_groups/create/",
            dict(
                users=[self.user.pk, self.user2.pk, self.user3.pk],
                title="강남역 12월모임",
            ),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["is_direct_message"], False)
        self.assertEqual(resp.json()["title"], "강남역 12월모임")

    def test_cannot_create_direct_message_to_protected(self):
        self.user.is_protected = True
        self.user.save()
        is_valid = MessageService.is_valid_to_create(self.user, self.user2)
        self.assertEqual(is_valid, True)
        is_valid = MessageService.is_valid_to_create(self.user2, self.user)
        self.assertEqual(is_valid, False)

        FollowService(self.user2).follow(self.user)
        FollowService(self.user).follow(self.user2)

        is_valid = MessageService.is_valid_to_create(self.user, self.user2)
        self.assertEqual(is_valid, True)

    def test_add_user(self):
        service = MessageService.get_or_create(
            self.user,
            self.user2,
            self.user3,
            is_direct_message=False,
            title="group_message",
        )
        u = User.objects.create(
            username="test4",
            nickname="test4",
            email="test4@test.com",
            is_protected=True,
        )
        is_error = self.aware_error(service.add_user)(self.user, u)
        self.assertEqual(is_error.is_error, True)

        u.is_protected = False
        u.save()
        is_error = self.aware_error(service.add_user)(self.user, u)
        self.assertEqual(is_error.is_error, False)

        self.assertEqual(service.group.attendants.count(), 4)

        service.exit_room(u)
        self.assertEqual(service.group.attendants.count(), 3)


class TestMessage(TestCase):
    def test_message_check(self):
        self.client.login(self.user)
        resp = self.client.post(
            "/message_groups/create/", dict(users=[self.user.pk, self.user2.pk])
        )
        self.assertEqual(resp.status_code, 201)
        s1 = MessageService(MessageGroup.objects.get(pk=resp.json()["id"]))
        self.assertEqual(MessageService.get_unreaded_message(self.user).exists(), False)
        # 그룹메세지 보내기
        self.client.post(
            f"/message_groups/{s1.group.pk}/send_message/", dict(message="1")
        )
        self.assertEqual(MessageService.get_unreaded_message(self.user).exists(), False)
        self.assertEqual(MessageService.get_unreaded_message(self.user2).exists(), True)
        self.assertEqual(
            MessageService.get_unreaded_message(self.user3).exists(), False
        )
        resp = self.client.get(f"/message_groups/{s1.group.pk}/")
        self.assertEqual(resp.json().get("unreaded_messages"), 0)
        self.client.login(self.user2)
        resp = self.client.get(f"/message_groups/{s1.group.pk}/")
        self.assertEqual(resp.json().get("unreaded_messages"), 1)

        s1.check_message(self.user)
        self.assertEqual(MessageService.get_unreaded_message(self.user).exists(), False)
        self.assertEqual(MessageService.get_unreaded_message(self.user2).exists(), True)
        self.assertEqual(
            MessageService.get_unreaded_message(self.user3).exists(), False
        )

        self.client.login(self.user2)
        resp = self.client.get(f"/message_groups/{s1.group.pk}/")
        self.assertEqual(resp.json().get("unreaded_messages"), 1)

        self.client.login(self.user)
        resp = self.client.get(f"/message_groups/{s1.group.pk}/")
        self.assertEqual(resp.json().get("unreaded_messages"), 0)
        resp = self.client.get(f"/message_groups/{s1.group.pk}/messages/")
        self.assertEqual(resp.status_code, 200)
