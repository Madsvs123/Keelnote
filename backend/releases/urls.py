from rest_framework.routers import DefaultRouter

from .views import EntryViewSet, ProductViewSet, VersionViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("versions", VersionViewSet, basename="version")
router.register("entries", EntryViewSet, basename="entry")

urlpatterns = router.urls
