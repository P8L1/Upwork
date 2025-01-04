# leaderboards/management/commands/create_test_users.py

import json
import random
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from accounts.models import CustomUser
from leaderboards.models import League, LeagueGroup, UserLeaguePlacement
from leaderboards.league_service import LEAGUE_CAPACITY

class Command(BaseCommand):
    help = "Create a specified number of test users with password=123. Distributes them across all leagues, not just Bronze."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1000,
            help='Number of test users to create (default: 1000)',
        )
        parser.add_argument(
            '--json-file',
            type=str,
            default="users_created.json",
            help="Filename for the JSON output of newly created users",
        )

    def handle(self, *args, **options):
        count = options['count']
        json_filename = options['json_file']

        self.stdout.write(self.style.WARNING(f"Creating {count} test users..."))

        # Step 1: Create test users
        created_users = []
        for i in range(count):
            username = f"test_user_{i}"
            email = f"user{i}@test.com"
            password = "123"  # Properly hashed by create_user
            gems_count = random.randint(0, 500)
            exp_this_league = random.randint(0, 10000)

            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                username=username,
                gems_count=gems_count,
                exp_this_league=exp_this_league,
            )

            # We'll store data for the JSON
            created_users.append({
                "username": username,
                "email": email,
                "gems_count": gems_count,
                "current_league": user.current_league,
                "exp_this_league": user.exp_this_league,
            })

        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} test users!"))

        # Step 2: Assign users to leagues (if not skipped)

        self.assign_users_to_leagues()

        # Step 3: Write newly created users to JSON
        with open(json_filename, "w") as f:
            json.dump(created_users, f, indent=4)
        self.stdout.write(self.style.SUCCESS(f"Wrote user data to {json_filename}"))

    def assign_users_to_leagues(self):
        """
        Distribute users across all existing leagues, 
        so that each league gets roughly the same number of users.
        or you can do a random approach.
        """
        all_leagues = list(League.objects.order_by("order"))
        if not all_leagues:
            self.stdout.write(self.style.WARNING("No leagues found. Aborting league assignment."))
            return

        # We define the "week_start" as current Monday, for example:
        week_start = (now().date() - timedelta(days=now().weekday()))

        users = list(CustomUser.objects.order_by("-exp_this_league"))

        self.stdout.write(self.style.WARNING(
            f"Assigning {len(users)} users among {len(all_leagues)} leagues..."
        ))

        # -------------------------
        # Option A: Uniform distribution by chunk
        # -------------------------
        chunk_size = max(1, len(users) // len(all_leagues))
        league_index = 0

        for i, user in enumerate(users):
            # Once we fill chunk_size, move to the next league
            if i != 0 and i % chunk_size == 0:
                league_index += 1
            if league_index >= len(all_leagues):
                league_index = len(all_leagues) - 1  # put overflow in last league

            league_obj = all_leagues[league_index]
            self.place_user_in_league_group(user, league_obj, week_start)

        # -------------------------
        # Option B: Random approach (uncomment if you prefer random)
        # -------------------------
        # for user in users:
        #     league_obj = random.choice(all_leagues)
        #     self.place_user_in_league_group(user, league_obj, week_start)

        self.stdout.write(self.style.SUCCESS("All users have been distributed among leagues."))

    def place_user_in_league_group(self, user, league_obj, week_start):
        """
        Find or create an open league group for the given league_obj at this week_start.
        Then place the user in it.
        """
        existing_groups = LeagueGroup.objects.filter(
            league=league_obj,
            week_start=week_start
        ).order_by("id")

        # find a group with space
        for group in existing_groups:
            if group.placements.count() < LEAGUE_CAPACITY:
                self._assign_user_to_group(user, group, league_obj.name)
                return

        # else create new group
        new_group = LeagueGroup.objects.create(league=league_obj, week_start=week_start)
        self._assign_user_to_group(user, new_group, league_obj.name)

    def _assign_user_to_group(self, user, group, league_name):
        UserLeaguePlacement.objects.create(
            user=user,
            league_group=group,
            exp_earned=user.exp_this_league,
        )
        user.current_league = league_name
        user.save()
        self.stdout.write(
            self.style.SUCCESS(f"Assigned user {user.username} to league {league_name}")
        )
