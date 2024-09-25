from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from commons.model_utils import make_property_field
from users.models import User, models
from ..models import Post, Favorite, Bookmark, Repost


class PostService:
    def __init__(self, user: User):
        self.user = user

    # 1. 리포스트 가운데 자신이 팔로우한 유저의 게시물을 가져와야됨.
