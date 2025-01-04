# leaderboards/tests/test_league_reset.py

from django.test import TestCase
from django.utils import timezone
import random
from accounts.models import CustomUser
from leaderboards.models import League, LeagueGroup, UserLeaguePlacement, UserWeeklyOutcome
from leaderboards.league_service import reset_leagues, place_new_user_in_bronze, LEAGUES_ORDER

class LeagueResetTest(TestCase):
    def setUp(self):
        # Create leagues
        for i, name in enumerate(LEAGUES_ORDER):
            League.objects.create(name=name, icon="league_icons/default.png", order=i)
        
        # Create 1000 users
        self.users = []
        for i in range(1000):
            email = f"testuser{i}@example.com"
            user = CustomUser.objects.create_user(email=email, password="1234")
            user.username = f"testuser{i}"
            user.exp_this_league = random.randint(0, 200)
            user.save()
            self.users.append(user)

    def test_full_league_reset(self):
        # Place them in Bronze
        for user in self.users:
            place_new_user_in_bronze(user)

        old_groups_count = LeagueGroup.objects.count()

        # Run reset
        reset_leagues()

        new_groups_count = LeagueGroup.objects.count()

        # Basic checks
        self.assertTrue(new_groups_count >= old_groups_count, 
                        "We expect new groups to be created for the new cycle (or at least a new set).")

        # Check that each user either has a new league or is locked out
        for user in self.users:
            # If user.current_league != "" => they should have a new placement
            # or they might be locked out => user.current_league == ""
            # We can also check for an outcome record
            has_outcome = UserWeeklyOutcome.objects.filter(user=user).exists()
            self.assertTrue(has_outcome, f"User {user.username} missing outcome record")
        
        print("Test completed successfully with 1000 users.")
