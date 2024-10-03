from rest_framework import routers

from .views import MessageGroupViewset

router = routers.DefaultRouter()
router.register("message_groups", MessageGroupViewset)


urlpatterns = router.urls
