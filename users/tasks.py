from uuid import uuid4

from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from commons.celery import shared_task
from .models import User


@shared_task()
def delete_unregistered_user(user_id: int):
    print(user_id)
    return


@shared_task()
def send_register_email(user_id: int, code_key: str):
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return

    rendered_text = render_to_string(
        "auth/signup_email.html",
        context=dict(
            user=user,
            front_end_host="http://localhost:3000",
            front_end_auth_url="authorize",
            front_end_auth_key="code_key",
            code_key=code_key,
        ),
    )
    msg = EmailMultiAlternatives(
        "Cotton에 오신것을 환영합니다",
        rendered_text,
        settings.EMAIL_HOST_USER,
        [user.email],
    )
    msg.attach_alternative(rendered_text, "text/html")
    msg.send()
