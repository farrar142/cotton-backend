from rest_framework import routers
from .views import NotificationViewSet

router = routers.DefaultRouter()
router.register("notifications", NotificationViewSet)


urlpatterns = router.urls
