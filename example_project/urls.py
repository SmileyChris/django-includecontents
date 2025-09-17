"""
URL configuration for example_project.
"""

from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("showcase/", include("showcase.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
