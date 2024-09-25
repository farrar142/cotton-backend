from rest_framework.routers import DefaultRouter

from .views import UserViewSet, AuthViewSet

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("auth", AuthViewSet, basename="auth")


urlpatterns = [*router.urls]
