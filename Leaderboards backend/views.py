# leaderboards/views.py

import logging

logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils.timezone import now
from datetime import timedelta, timezone

from .models import LeagueGroup, UserLeaguePlacement, League, UserWeeklyOutcome
from .serializers import UserPlacementSerializer, LeagueSerializer
from accounts.models import CustomUser
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Import these helpers from your league_service.py (adjust path if needed)
from .league_service import get_next_monday_0001_utc, get_previous_monday_0001_utc


class CurrentLeagueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.debug(f"[CurrentLeagueView] user={user.id} {user.username}")

        current_time = now()
        monday_start_dt = get_previous_monday_0001_utc(current_time)
        monday_start_date = monday_start_dt.date()
        logger.debug(f"[CurrentLeagueView] monday_start_dt={monday_start_dt}, monday_start_date={monday_start_date}")

        lowest_league = League.objects.order_by("order").first()
        if not lowest_league:
            logger.error("[CurrentLeagueView] No leagues defined.")
            return Response({"error": "No leagues defined."}, status=500)

        logger.debug(f"[CurrentLeagueView] lowest_league={lowest_league.name}")


        locked_out = (user.current_league == "")
        if locked_out:
            return Response({
                "locked_out": True,
                "outcome": {
                    "finished_rank": 0,
                    "old_league": "",
                    "new_league": "",
                },
                "currentLeague": "",  # no league
                "leaderboard": [],
                "leagues": [],        # or send them anyway if you want
                "countdown_seconds": 0,
            })

        placement = (
            UserLeaguePlacement.objects
            .filter(user=user, league_group__week_start=monday_start_date)
            .select_related("league_group__league")
            .first()
        )
        if not placement:
            logger.debug(f"[CurrentLeagueView] No placement found for user={user.id} in week_start={monday_start_date}")
            league_group, _ = LeagueGroup.objects.get_or_create(
                league=lowest_league, week_start=monday_start_date
            )
            logger.debug(f"[CurrentLeagueView] league_group={league_group}, created={_}")
            placement = UserLeaguePlacement.objects.create(
                user=user, league_group=league_group, exp_earned=0
            )
            logger.info(f"[CurrentLeagueView] Created new placement for user={user.username} in {lowest_league.name}")
        else:
            logger.debug(f"[CurrentLeagueView] Found placement: {placement}")

        if placement.exp_earned != user.exp_this_league:
            logger.debug(f"[CurrentLeagueView] Updating placement EXP for user={user.username}")
            placement.exp_earned = user.exp_this_league
            placement.save()

        group_placements = (
            UserLeaguePlacement.objects
            .filter(league_group=placement.league_group)
            .select_related("user")
        )
        logger.debug(f"[CurrentLeagueView] group_placements count={len(group_placements)}")
        for p in group_placements:
            logger.debug(f"[CurrentLeagueView] User={p.user.username}, exp_earned={p.exp_earned}")

        sorted_placements = sorted(group_placements, key=lambda x: x.exp_earned, reverse=True)
        logger.debug(f"[CurrentLeagueView] Sorted placements: {[p.user.username for p in sorted_placements]}")

        ranked_serialized = []
        for index, p in enumerate(sorted_placements):
            data = UserPlacementSerializer(p).data
            data["rank"] = index + 1
            ranked_serialized.append(data)

        all_leagues = League.objects.order_by("order")
        logger.debug(f"[CurrentLeagueView] Total leagues count={all_leagues.count()}")
        for league in all_leagues:
            logger.debug(f"[CurrentLeagueView] League: {league.name}, order={league.order}")

        leagues_serialized = LeagueSerializer(all_leagues, many=True).data

        next_monday_dt = get_next_monday_0001_utc(current_time)
        delta = next_monday_dt - current_time.astimezone(timezone.utc)
        countdown_seconds = delta.total_seconds()
        if countdown_seconds < 0:
            countdown_seconds = 0

        logger.debug(f"[CurrentLeagueView] current_time={current_time}, next_monday_dt={next_monday_dt}, countdown_seconds={countdown_seconds}")

        outcome_data = {"finished_rank": 0, "old_league": "", "new_league": ""}
        try:
            outcome = user.userweeklyoutcome
            outcome_data = {
                "finished_rank": outcome.finished_rank,
                "old_league": outcome.old_league,
                "new_league": outcome.new_league,
            }
        except:
            pass

        response_data = {
            "currentLeague": placement.league_group.league.name,
            "outcome": outcome_data,
            "leaderboard": ranked_serialized,
            "leagues": leagues_serialized,
            "countdown_seconds": countdown_seconds,
            "server_time_utc": now().astimezone(timezone.utc).isoformat(),
        }
        logger.debug(f"[CurrentLeagueView] Response data: {response_data}")

        return Response(response_data)


    def send_leaderboard_update(user):
        placements = (
            UserLeaguePlacement.objects.filter(league_group__users=user)
            .select_related("user", "league_group__league")
            .order_by("-exp_earned")
        )

        for placement in placements:
            if placement.exp_earned != placement.user.exp_this_league:
                placement.exp_earned = placement.user.exp_this_league
                placement.save()

        leaderboard = [
            {
                "username": placement.user.username,
                "email": placement.user.email,
                "exp_earned": placement.exp_earned,
                "rank": idx + 1,
            }
            for idx, placement in enumerate(placements)
        ]

        current_league = (
            placements.first().league_group.league.name if placements.exists() else "Unknown League"
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"leaderboard_{user.id}",
            {
                "type": "send_leaderboard_update",
                "leaderboard": leaderboard,
                "current_league": current_league,
            },
        )
