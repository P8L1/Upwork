# leaderboards/management/commands/test_league_reset.py

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser
from leaderboards.models import League, LeagueGroup, UserLeaguePlacement, UserWeeklyOutcome
from leaderboards.league_service import reset_leagues, LEAGUES_ORDER, place_new_user_in_bronze

class Command(BaseCommand):
    help = "Creates 1000 users, assigns random XP, places them into leagues, and runs reset_leagues()."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting test_league_reset..."))

        # 1) Ensure we have all the leagues in the DB that match LEAGUES_ORDER
        self._create_leagues_if_needed()

        # 2) Create 1,000 users (or however many you want). If they exist, we skip creation.
        total_users = 1000
        self.stdout.write(f"Ensuring {total_users} test users exist...")
        for i in range(total_users):
            email = f"testuser{i}@example.com"
            user, created = CustomUser.objects.get_or_create(email=email)
            if created:
                user.set_password("1234")
                user.username = f"testuser{i}"
                user.save()

        # 3) Assign random exp_this_league to each user and optionally place them
        #    in random leagues (or we can place them all in Bronze for the test).
        self.stdout.write("Assigning random exp_this_league to all test users...")
        all_users = CustomUser.objects.filter(email__startswith="testuser")
        for user in all_users:
            user.exp_this_league = random.randint(0, 200)  # some random range
            user.save()

        # 4) Place each user in Bronze (or random league). 
        #    For demonstration, we’ll put them in Bronze if they’re not locked out.
        self.stdout.write("Placing users into Bronze if they are not locked out (exp_to_enter < 40).")
        for user in all_users:
            # Optionally randomize user.exp_to_enter to test the locked-out logic
            if user.exp_to_enter == 0:
                # let’s randomize 0 or 40
                user.exp_to_enter = random.choice([0, 40])
                user.save()

            # Now place them if possible
            place_new_user_in_bronze(user)

        # 5) Check how many LeagueGroups exist prior to reset
        existing_groups_count = LeagueGroup.objects.count()

        self.stdout.write(f"Before reset, we have {existing_groups_count} league group(s).")

        # 6) Run reset_leagues
        self.stdout.write("Running reset_leagues()...")
        reset_leagues()

        # 7) Check how many new LeagueGroups got created
        new_groups_count = LeagueGroup.objects.count()
        self.stdout.write(f"After reset, we have {new_groups_count} league group(s).")

        # 8) Basic validation:
        #    - Do all 1000 users have a placement for the *new* cycle?
        #    - Did each user get a UserWeeklyOutcome?
        outcome_missing_count = 0
        new_cycle_league_missing_count = 0

        for user in all_users:
            # Check outcome
            has_outcome = UserWeeklyOutcome.objects.filter(user=user).exists()
            if not has_outcome:
                outcome_missing_count += 1

            # Check if the user got placed in the new cycle (week_start == new_monday_start_dt)
            # Or if locked out with user.current_league == "" => that’s also valid, but we’ll see if
            # we consider that "missing" or not.
            # For now, we just see if they have a new placement.
            # (In your code, they may have been removed if they are locked out.)
            placement_exists = UserLeaguePlacement.objects.filter(user=user).exists()
            if not placement_exists and user.current_league != "":
                new_cycle_league_missing_count += 1

        self.stdout.write(self.style.NOTICE(
            f"Out of {total_users} users, {outcome_missing_count} missing a UserWeeklyOutcome. "
            f"{new_cycle_league_missing_count} missing new league placement (but not locked out)."
        ))

        self.stdout.write(self.style.SUCCESS("test_league_reset completed successfully!"))


    def _create_leagues_if_needed(self):
        self.stdout.write("Ensuring DB has all leagues matching LEAGUES_ORDER...")

        for i, league_name in enumerate(LEAGUES_ORDER):
            league, created = League.objects.get_or_create(
                name=league_name,
                defaults={
                    "order": i,
                    "icon": "league_icons/default.png",  # or some placeholder
                },
            )
            if created:
                self.stdout.write(f"  Created league: {league.name} (order={i})")
            else:
                # Update order if needed
                if league.order != i:
                    league.order = i
                    league.save()
                    self.stdout.write(f"  Updated league: {league.name} -> order={i}")

