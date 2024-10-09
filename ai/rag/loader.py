import json
from typing import TYPE_CHECKING
from langchain_core.documents import Document
from langchain_community.document_loaders.base import BaseLoader

if TYPE_CHECKING:
    from users.models import User
    from posts.models import Post


def _build_metadata(post: "Post"):
    parent = post.parent.pk if post.parent else None
    return {
        "source": post.pk,
        "created_at": post.created_at.isoformat(),
        "user": post.user_id,
        "parent": parent,
        "id": post.pk,
        "nickname": post.user.nickname,
    }


class PostLoader(BaseLoader):
    def __init__(self, user: "User", posts: "list[Post]"):
        self.items = posts
        self.user = user

    def load(self) -> list[Document]:
        from posts.serializers import PostSerializer

        return [
            Document(
                page_content=json.dumps(PostSerializer(item, user=self.user).data),
                metadata=_build_metadata(item),
            )
            for item in self.items
        ]
