"""
URL configuration for fantaweek project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from application import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index_view, name="index"),
    path("logout", views.logout_view, name="logout"),
    path("upload_file", views.upload_file_view, name="upload_file"),
    path("download_db", views.download_db_view, name="download_db"),
    path("add_agency", views.add_agency_view, name="add_agency"),
    path("block_agency", views.block_agency_view, name="block_agency"),
    path("modify_agency", views.modify_agency_view, name="modify_agency"),
    path("add_player", views.add_player_view, name="add_player"),
    path("modify_player", views.modify_player_view, name="modify_player"),
    path("create_team", views.create_team_view, name="create_team"),
    path("subscribe_tournament", views.subscribe_tournament_view, name="subscribe_tournament"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
