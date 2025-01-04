# leaderboards/urls.py

from django.urls import path
from .views import CurrentLeagueView


urlpatterns = [
    path("current-league/", CurrentLeagueView.as_view(), name="current-league"),
]


