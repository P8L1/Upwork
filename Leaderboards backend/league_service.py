# league_service.py

import logging
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now
from datetime import datetime, timedelta, time, timezone

from .models import League, LeagueGroup, UserLeaguePlacement, UserWeeklyOutcome
from accounts.models import CustomUser
from celery import shared_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LEAGUE_CAPACITY = 30
PROMOTED_COUNT = 7
DEMOTED_COUNT = 7

LEAGUES_ORDER = [
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Diamond",
    "Sapphire",
    "Ruby",
    "Emerald",
    "Onyx",
    "Obsidian",
]

DIAMOND_GEM_REWARD = 50
EXP_TO_REJOIN = 40


@shared_task
def reset_leagues_task():
    try:
        reset_leagues()
    except Exception as e:
        logger.error(f"[reset_leagues_task] League reset failed: {e}")


def get_league_map():
    league_map = {}
    for league in League.objects.all():
        league_map[league.name] = league
    return league_map


def get_previous_monday_0001_utc(ref_dt=None):
    if ref_dt is None:
        ref_dt = now()
    ref_utc = ref_dt.astimezone(timezone.utc)
    days_since_monday = ref_utc.isoweekday() - 1  # Monday=1
    monday_date = (ref_utc - timedelta(days=days_since_monday)).date()
    monday_0001 = datetime.combine(monday_date, time(0, 1), tzinfo=timezone.utc)
    if ref_utc < monday_0001:
        monday_0001 -= timedelta(days=7)
    return monday_0001


def get_next_monday_0001_utc(ref_dt=None):
    if ref_dt is None:
        ref_dt = now()
    ref_utc = ref_dt.astimezone(timezone.utc)
    weekday = ref_utc.isoweekday()
    days_until = (8 - weekday) if weekday != 1 else 7
    next_monday = datetime.combine(
        (ref_utc + timedelta(days=days_until)).date(), time(0, 1), tzinfo=timezone.utc
    )
    if ref_utc >= next_monday:
        next_monday += timedelta(days=7)
    return next_monday


@transaction.atomic
def place_new_user_in_bronze(user):
    """Places user in Bronze if exp_to_enter < EXP_TO_REJOIN, filling existing groups first."""
    if user.exp_to_enter >= EXP_TO_REJOIN:
        logger.info(f"User '{user.username}' locked out (needs {user.exp_to_enter}).")
        return

    bronze_league = League.objects.filter(name=LEAGUES_ORDER[0]).first()
    if not bronze_league:
        logger.warning("No Bronze league found!")
        return

    dt_utc = now().astimezone(timezone.utc)
    weekday = dt_utc.isoweekday()
    base_monday = (dt_utc - timedelta(days=weekday - 1)).date()
    monday_0001 = datetime.combine(base_monday, time(0, 1), tzinfo=timezone.utc)
    if dt_utc < monday_0001:
        base_monday -= timedelta(days=7)

    existing_groups = LeagueGroup.objects.filter(
        league=bronze_league, week_start=base_monday
    ).order_by("id")

    for group in existing_groups:
        if group.placements.count() < LEAGUE_CAPACITY:
            _place_user_in_group(user, group, LEAGUES_ORDER[0])
            return

    # Create a new Bronze group if none have space
    new_group = LeagueGroup.objects.create(
        league=bronze_league, week_start=base_monday
    )
    _place_user_in_group(user, new_group, LEAGUES_ORDER[0])


def _place_user_in_group(user, league_group, league_name):
    user.exp_this_league = 0
    user.current_league = league_name
    if user.exp_to_enter >= EXP_TO_REJOIN:
        user.exp_to_enter = 0
    user.save()

    UserLeaguePlacement.objects.create(user=user, league_group=league_group, exp_earned=0)
    logger.debug(f"Placed {user.username} in group {league_group.id}, league {league_name}")


@transaction.atomic
def reset_leagues():
    """1) Update locked-out users. 2) Process old cycle groups. 3) Reassign promotions/demotions."""
    league_map = get_league_map()
    if not league_map:
        logger.warning("No leagues in DB, aborting.")
        return

    # Step 1: handle locked-out users
    locked_out_users = CustomUser.objects.filter(current_league="")
    logger.info(f"[reset_leagues] {locked_out_users.count()} locked-out user(s).")

    for user in locked_out_users:
        if user.exp_to_enter >= EXP_TO_REJOIN:
            place_new_user_in_bronze(user)
        else:
            # Remain locked out, reset exp_to_enter
            user.exp_to_enter = 0
            user.save()

    # Step 2: process old groups
    ref_dt = now()
    old_monday = get_previous_monday_0001_utc(ref_dt)
    new_monday = old_monday + timedelta(days=7)

    old_groups = LeagueGroup.objects.filter(week_start=old_monday.date())
    if not old_groups.exists():
        logger.warning("No groups for old cycle, aborting.")
        return

    logger.info(f"[reset_leagues] old_cycle={old_monday}, new_cycle={new_monday}")

    for group in old_groups:
        old_league = group.league
        old_name = old_league.name

        # Exclude locked-out users
        placements = list(
            UserLeaguePlacement.objects.filter(league_group=group)
            .select_related("user")
            .exclude(user__current_league="")
        )
        if not placements:
            logger.info(f"Group {group.id} has no non-locked users.")
            continue

        placements.sort(key=lambda p: p.exp_earned, reverse=True)
        size = len(placements)
        logger.info(f"Processing group {group.id} ({old_name}), size={size}")

        if size < 7:
            top_list = placements[:]
            middle_list = []
            bottom_list = []
        elif size < 24:
            top_list = placements[:7]
            middle_list = placements[7:]
            bottom_list = []
        else:
            top_list = placements[:7]
            middle_list = placements[7 : size - 7]
            bottom_list = placements[size - 7 :]

        # Obsidian gem reward
        if old_name == "Obsidian":
            for p in top_list:
                p.user.gems_count += DIAMOND_GEM_REWARD
                p.user.save()

        old_index = LEAGUES_ORDER.index(old_name)
        promoted_league_name = (
            LEAGUES_ORDER[old_index + 1]
            if old_index < len(LEAGUES_ORDER) - 1
            else old_name
        )
        demoted_league_name = (
            LEAGUES_ORDER[old_index - 1] if old_index > 0 else old_name
        )

        # Bronze removal if bottom or 0 XP
        if old_name == LEAGUES_ORDER[0]:
            for p in bottom_list:
                p.user.exp_to_enter = EXP_TO_REJOIN
                p.user.current_league = ""
                p.user.save()
            for p in placements:
                if p.exp_earned == 0:
                    p.user.exp_to_enter = EXP_TO_REJOIN
                    p.user.current_league = ""
                    p.user.save()

        promoted_set = [p.user for p in top_list]
        remain_set = [p.user for p in middle_list]
        demoted_set = []

        if old_name != LEAGUES_ORDER[0]:
            demoted_set = [p.user for p in bottom_list]

        # Weekly outcomes
        for idx, p in enumerate(placements):
            final_rank = idx + 1
            user = p.user
            if p in top_list:
                new_l = promoted_league_name if old_index < len(LEAGUES_ORDER) - 1 else old_name
            elif p in bottom_list:
                new_l = "" if old_index == 0 else demoted_league_name
            else:
                new_l = old_name

            UserWeeklyOutcome.objects.update_or_create(
                user=user,
                defaults={
                    "finished_rank": final_rank,
                    "old_league": old_name,
                    "new_league": new_l,
                },
            )

        assign_users_to_new_league(promoted_set, promoted_league_name, new_monday, league_map)
        assign_users_to_new_league(remain_set, old_name, new_monday, league_map)
        if old_name != LEAGUES_ORDER[0]:
            assign_users_to_new_league(demoted_set, demoted_league_name, new_monday, league_map)

    logger.info("Deleting old league groups.")
    old_groups.delete()
    logger.info("League reset completed.")


def assign_users_to_new_league(users, league_name, new_cycle_monday, league_map):
    if not users or league_name not in league_map:
        return

    league_obj = league_map[league_name]
    slice_start = 0
    while slice_start < len(users):
        slice_end = slice_start + LEAGUE_CAPACITY
        chunk = users[slice_start:slice_end]

        group = LeagueGroup.objects.create(
            league=league_obj,
            week_start=new_cycle_monday.date()
        )
        for u in chunk:
            u.current_league = league_name
            u.exp_this_league = 0
            u.save()
            UserLeaguePlacement.objects.create(user=u, league_group=group, exp_earned=0)

        slice_start += LEAGUE_CAPACITY
