from django.template.loader import render_to_string
from base.test import TestCase

from commons.authentication import CustomTokenObtainPairSerializer

# Create your tests here.
from .models import User, models
from .services import AuthService


class TestUser(TestCase):

    def setUp(self):
        pass

    def test_user_create(self):
        user = User(username="test", email="test@gmail.com")
        user.set_password("1234567890")
        user.save()

    def test_user_signup(self):
        data = dict(
            email="test@gmail.com",
            username="testuser",
            password="1234567890",
            password2="1234567890",
        )
        resp = self.client.post("/auth/signup/", data=data)
        self.assertEqual(resp.status_code, 201)

    def test_user_siginin(self):
        user = User(username="test", email="test@gmail.com")
        user.set_password("1234567890")
        user.save()

        self.client.login(user=user)
        resp = self.client.get("/users/me/")
        self.assertEqual(resp.status_code, 200)

    def test_refresh(self):

        user = User(username="test", email="test@gmail.com")
        user.set_password("1234567890")
        user.save()

        access, refresh = self.client.login(user=user)  # type:ignore
        resp = self.client.post(
            "/auth/refresh/",
            data=dict(refresh=refresh),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)


# 1. 유저가 생성되면 1시간 뒤에 유저를 삭제하는 셀러리 태스크를 생성
class TestEmailAuthorization(TestCase):
    def setUp(self):

        service = AuthService
        self.user, tokens = service.signup(
            email="test@gmail.com",
            username="test",
            password="123456789",
            password2="123456789",
        )
        self.user2, tokens = service.signup(
            email="test2@gmail.com",
            username="test2",
            password="123456789",
            password2="123456789",
        )
        self.user3, tokens = service.signup(
            email="test3@gmail.com",
            username="test3",
            password="123456789",
            password2="123456789",
        )

    # def test_html(self):
    #     rendered_text = render_to_string(
    #         "auth/signup_email.html", context=dict(user=self.user)
    #     )
    def test_유저_인증_테스트(self):
        self.assertEqual(self.user.is_registered, False)
        s = AuthService(self.user)
        code_key = s.send_register_email()
        AuthService.register_user(code_key=code_key)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_registered, True)
