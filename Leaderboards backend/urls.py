# leaderboards/urls.py

from django.urls import path
from .views import CurrentLeagueView
from .consumers import LeaderboardConsumer

urlpatterns = [
    path("current-league/", CurrentLeagueView.as_view(), name="current-league"),
    path("ws/leaderboard/", LeaderboardConsumer.as_asgi()),
]

websocket_urlpatterns = [
    path("ws/leaderboard/", LeaderboardConsumer.as_asgi()),
]
