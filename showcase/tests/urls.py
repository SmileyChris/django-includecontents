from django.urls import include, path

urlpatterns = [
    path("showcase/", include("showcase.urls")),
]
