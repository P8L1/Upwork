# leaderboards/serializers.py

from rest_framework import serializers
from .models import UserLeaguePlacement, League, LeagueGroup
from accounts.models import CustomUser


class LeaderboardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["username", "email"]


class UserPlacementSerializer(serializers.ModelSerializer):
    user = LeaderboardUserSerializer()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = UserLeaguePlacement
        fields = ["user", "exp_earned", "rank"]

    def get_rank(self, obj):
        return self.context.get("rank", None)


class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ["name", "icon", "order"]


class LeagueGroupSerializer(serializers.ModelSerializer):
    league = LeagueSerializer()

    class Meta:
        model = LeagueGroup
        fields = ["league", "week_start"]
