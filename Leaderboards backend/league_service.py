# leaderboards/league_service.py

import logging
from django.db import transaction
from django.utils.timezone import now
from datetime import datetime, timedelta, time, timezone

from .models import League, LeagueGroup, UserLeaguePlacement
from accounts.models import CustomUser
from celery import shared_task

logger = logging.getLogger(__name__)

LEAGUE_CAPACITY = 30
PROMOTED_COUNT = 7
DEMOTED_COUNT = 7

LEAGUES_ORDER = [
    "Bronze Calculators",
    "Silver Integrals",
    "Gold Derivatives",
    "Platinum Limits",
    "Diamond Functions",
    "Sapphire Gradients",
    "Ruby Series",
    "Emerald Tangents",
    "Onyx Infinites",
    "Obsidian Theorems",
]


@shared_task
def reset_leagues_task():
    """
    Celery task to reset leagues every Monday at 00:01 GMT.
    You can configure Celery beat so that it calls this task
    right around that time, or slightly after.
    """
    try:
        reset_leagues()
    except Exception as e:
        logger.error(f"[reset_leagues_task] League reset failed: {e}", exc_info=True)


def get_league_map():
    """
    Returns a dict of {league_name: league_object}.
    """
    league_map = {}
    for league in League.objects.all():
        league_map[league.name] = league
    return league_map


def get_previous_monday_0001_utc(reference_datetime=None):
    """
    Finds the most recent Monday at 00:01 UTC before or equal to reference_datetime.
    This is used as the 'old week start'.
    """
    if reference_datetime is None:
        reference_datetime = now()

    reference_utc = reference_datetime.astimezone(timezone.utc)
    weekday = reference_utc.isoweekday()  # Monday=1
    days_since_monday = weekday - 1

    monday_date = (reference_utc - timedelta(days=days_since_monday)).date()
    monday_0001 = datetime.combine(monday_date, time(0, 1), tzinfo=timezone.utc)
    if reference_utc < monday_0001:
        monday_0001 -= timedelta(days=7)

    return monday_0001


def get_next_monday_0001_utc(reference_datetime=None):
    """
    Finds the upcoming Monday at 00:01 UTC after reference_datetime.
    This is the 'new week start'.
    """
    if reference_datetime is None:
        reference_datetime = now()

    reference_utc = reference_datetime.astimezone(timezone.utc)
    weekday = reference_utc.isoweekday()  # Monday=1
    days_until_next_monday = (8 - weekday) if weekday != 1 else 7

    next_monday_date = (reference_utc + timedelta(days=days_until_next_monday)).date()
    next_monday_0001 = datetime.combine(next_monday_date, time(0, 1), tzinfo=timezone.utc)

    if reference_utc >= next_monday_0001:
        next_monday_0001 += timedelta(days=7)

    return next_monday_0001


@transaction.atomic
def place_new_user_in_bronze(user):
    """
    Places a new user into a Bronze league group for the current cycle:
      1) If there's a Bronze group <30 members, put them there.
      2) Otherwise, create a new Bronze group.
      3) user.exp_this_league=0, user.current_league='Bronze Calculators', etc.
    """
    # We'll assume the first item in LEAGUES_ORDER is Bronze
    bronze_name = LEAGUES_ORDER[0]  # "Bronze Calculators"
    bronze_league = League.objects.filter(name=bronze_name).first()
    if not bronze_league:
        logger.error(f"No Bronze league found with name='{bronze_name}'!")
        return

    # Compute the "current" Monday at 00:01
    reference_utc = now().astimezone(timezone.utc)
    weekday = reference_utc.isoweekday()  # Monday=1
    days_since_monday = weekday - 1
    base_monday_date = (reference_utc - timedelta(days=days_since_monday)).date()
    monday_0001 = datetime.combine(base_monday_date, time(0, 1), tzinfo=timezone.utc)
    if reference_utc < monday_0001:
        base_monday_date -= timedelta(days=7)
    week_start = base_monday_date

    # Find existing Bronze groups for this cycle
    existing_bronze_groups = LeagueGroup.objects.filter(
        league=bronze_league,
        week_start=week_start
    ).order_by("id")

    for group in existing_bronze_groups:
        count_in_group = UserLeaguePlacement.objects.filter(league_group=group).count()
        if count_in_group < LEAGUE_CAPACITY:
            logger.debug(f"Placing new user '{user.username}' in existing Bronze group {group.id}")
            _place_user_in_group(user, group, bronze_name)
            return

    # If all existing Bronze groups are full, create a new one
    new_group = LeagueGroup.objects.create(
        league=bronze_league,
        week_start=week_start
    )
    logger.debug(f"Created new Bronze group {new_group.id} for user '{user.username}'")
    _place_user_in_group(user, new_group, bronze_name)


def _place_user_in_group(user, league_group, league_name):
    """
    Internal helper to place a user in a specific league_group.
    """
    user.exp_this_league = 0
    user.current_league = league_name
    user.save()

    UserLeaguePlacement.objects.create(
        user=user,
        league_group=league_group,
        exp_earned=0
    )


@transaction.atomic
def reset_leagues():
    """
    Resets league placements for a new Monday->Monday cycle:
      - Top 7 get promoted (unless in highest league => +50 gems).
      - Bottom 7 get demoted (unless in Bronze => fallback).
      - Everyone else remains.
      - Splits each league's users into groups of up to 30.
    """
    reference_datetime = now()
    old_monday_start = get_previous_monday_0001_utc(reference_datetime)
    new_monday_start = old_monday_start + timedelta(days=7)

    logger.info(
        f"[reset_leagues] Starting from old_monday={old_monday_start}, new_monday={new_monday_start}"
    )

    league_map = get_league_map()
    if not league_map:
        logger.error("[reset_leagues] No leagues in the system.")
        return

    # 1) Fetch old placements
    placements = (
        UserLeaguePlacement.objects
        .filter(league_group__week_start=old_monday_start.date())
        .select_related("user", "league_group__league")
    )
    logger.debug(f"Found {placements.count()} old placements for the previous cycle.")

    # user -> old_league_name
    old_league_map = {}
    for p in placements:
        old_league_map[p.user.id] = p.league_group.league.name

    # 2) group by league_group
    groups_by_league = {}
    for p in placements:
        groups_by_league.setdefault(p.league_group, []).append(p)

    # next_league_map: user.id -> league_name
    next_league_map = {}

    for lg, user_placements in groups_by_league.items():
        league_name = lg.league.name
        league_index = LEAGUES_ORDER.index(league_name)

        # Sort descending by exp_earned
        user_placements.sort(key=lambda x: x.exp_earned, reverse=True)

        # Identify next/previous league
        higher_league_name = (
            LEAGUES_ORDER[league_index + 1]
            if league_index + 1 < len(LEAGUES_ORDER)
            else None
        )
        lower_league_name = (
            LEAGUES_ORDER[league_index - 1]
            if league_index - 1 >= 0
            else None
        )

        for i, up in enumerate(user_placements):
            user = up.user
            rank = i + 1
            # top 7 => promote if possible
            if rank <= PROMOTED_COUNT:
                if higher_league_name:
                    next_league_map[user.id] = higher_league_name
                else:
                    # highest league => reward with +50
                    user.gems_count += 50
                    user.save()
                    next_league_map[user.id] = league_name
            # bottom 7 => demote if possible
            elif rank > len(user_placements) - DEMOTED_COUNT:
                if lower_league_name:
                    next_league_map[user.id] = lower_league_name
                else:
                    # Bronze fallback
                    next_league_map[user.id] = league_name
            else:
                # remain
                next_league_map[user.id] = league_name

    # 3) Bulk reassign
    users_by_target = {}
    all_users = CustomUser.objects.filter(id__in=next_league_map.keys())

    for user in all_users:
        league_name = next_league_map[user.id]
        users_by_target.setdefault(league_name, []).append(user)

    new_groups_count = 0
    new_week_date = new_monday_start.date()

    # For each league_name, chunk the user list by 30
    for league_name, user_list in users_by_target.items():
        # e.g. "Bronze Calculators" => get the League object
        league_obj = league_map[league_name]

        for i in range(0, len(user_list), LEAGUE_CAPACITY):
            slice_ = user_list[i : i + LEAGUE_CAPACITY]

            # create a new group for these 30 (or fewer)
            group = LeagueGroup.objects.create(
                league=league_obj,
                week_start=new_week_date
            )
            new_groups_count += 1

            # reset user exp, set current_league
            for u in slice_:
                u.exp_this_league = 0
                u.current_league = league_name
            CustomUser.objects.bulk_update(slice_, ["exp_this_league", "current_league"])

            # create new placements
            new_placements = []
            for u in slice_:
                new_placements.append(UserLeaguePlacement(
                    user=u, 
                    league_group=group, 
                    exp_earned=0
                ))
            UserLeaguePlacement.objects.bulk_create(new_placements)

    # 4) Log final movement
    # 4) Log final movement
    for user_id, old_lg in old_league_map.items():
        new_lg = next_league_map[user_id]
        if old_lg != new_lg:
            user = CustomUser.objects.get(id=user_id)  # Fetch the user to get the username
            logger.info(f"User {user.username} moved from {old_lg} => {new_lg}")


    logger.info(f"[reset_leagues] Completed. Created {new_groups_count} new groups.")
