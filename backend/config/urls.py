from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from releases.auth_views import HealthView, MeView, RegisterView

admin.site.site_header = "Keelnote"
admin.site.site_title = "Keelnote"
admin.site.index_title = "Release log"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view()),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/auth/token/", TokenObtainPairView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/", include("releases.urls")),
]
