from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("device/<str:device_id>/run/<str:command_id>/", views.run_command, name="run_command"),
    path("config/", views.config_view, name="config"),
]
