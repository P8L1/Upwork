# leaderboards/management/commands/create_test_users.py

import random
import string
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from datetime import timedelta

from accounts.models import CustomUser
from leaderboards.models import League, LeagueGroup, UserLeaguePlacement
from leaderboards.league_service import LEAGUE_CAPACITY  # If you want to match your existing constant

class Command(BaseCommand):
    help = "Create a specified number of test users, then assign them to random leagues with capacity-based logic."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1000,
            help='Number of test users to create (default: 1000)'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.WARNING(
            f"Creating {count} test users. Please wait..."
        ))

        # 1) Bulk-create the users
        users_to_create = []
        for i in range(count):
            # Generate a random suffix for the username, e.g. "test_user_ABC123_1"
            username = f"test_user_{i}"
            email = f"user{i}@test.com"  # Simple email format for test purposes
            password = "a"  # Fixed password
            
            # Create the user with random gems_count and exp_this_league
            user = CustomUser(
                username=username,
                email=email,
                gems_count=random.randint(0, 500),      
                exp_this_league=random.randint(0, 10000),
                password = password,
            )
            
            users_to_create.append(user)

        # Bulk create for speed
        CustomUser.objects.bulk_create(users_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {count} test users!"
        ))

        # 2) Now assign them to random leagues
        self.assign_users_to_leagues()

    def assign_users_to_leagues(self):
        """
        Distributes users across random leagues for *this week's* Monday,
        creating multiple LeagueGroups if needed, each up to LEAGUE_CAPACITY=30.
        """
        all_leagues = list(League.objects.order_by("order"))
        if not all_leagues:
            self.stdout.write(self.style.WARNING("No leagues found. Aborting league assignment."))
            return

        # Monday of the current week:
        week_start = (now().date() - timedelta(days=now().weekday()))

        # 1) Collect existing groups for this week_start
        #    We'll track how many users are currently in each group.
        existing_groups = LeagueGroup.objects.filter(week_start=week_start)
        groups_by_league = defaultdict(list)  
        # Will map league.id -> list of (group_obj, current_count)

        for grp in existing_groups:
            count_in_grp = UserLeaguePlacement.objects.filter(league_group=grp).count()
            groups_by_league[grp.league_id].append((grp, count_in_grp))

        # Sort each league's group list by ID, so we fill older groups first
        for league_id in groups_by_league:
            groups_by_league[league_id].sort(key=lambda x: x[0].id)

        all_users = CustomUser.objects.all()
        user_placements = []

        # 2) For each user, pick a random league
        for user in all_users:
            random_league = random.choice(all_leagues)

            assigned = False
            league_id = random_league.id
            group_list = groups_by_league[league_id]

            # Check if any existing group for that league has space
            for i, (g, current_count) in enumerate(group_list):
                if current_count < LEAGUE_CAPACITY:
                    # Place user here
                    user_placements.append(
                        UserLeaguePlacement(
                            user=user,
                            league_group=g,
                            exp_earned=user.exp_this_league,
                        )
                    )
                    # Update the in-memory count
                    group_list[i] = (g, current_count + 1)
                    assigned = True
                    break

            # If no group had space, create a new one
            if not assigned:
                new_group = LeagueGroup.objects.create(
                    league=random_league,
                    week_start=week_start
                )
                groups_by_league[league_id].append((new_group, 1))

                user_placements.append(
                    UserLeaguePlacement(
                        user=user,
                        league_group=new_group,
                        exp_earned=user.exp_this_league,
                    )
                )

        # 3) Bulk-create the placements
        UserLeaguePlacement.objects.bulk_create(user_placements)
        self.stdout.write(self.style.SUCCESS(
            f"Assigned {len(user_placements)} users to random leagues with capacity-based logic."
        ))
