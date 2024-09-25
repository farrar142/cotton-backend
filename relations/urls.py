from rest_framework import routers
from .views import FollowViewset

router = routers.DefaultRouter()
router.register("relations", FollowViewset)


urlpatterns = router.urls
