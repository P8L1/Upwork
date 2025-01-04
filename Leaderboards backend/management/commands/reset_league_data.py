from django.core.management.base import BaseCommand
from leaderboards.models import LeagueGroup, UserLeaguePlacement
from accounts.models import CustomUser
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Deletes all league groups, user placements, and resets users' leagues."

    def handle(self, *args, **kwargs):
        # Step 1: Delete all user placements
        self.stdout.write("Deleting all user placements...")
        UserLeaguePlacement.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All user placements deleted."))
        User = get_user_model()
        # Filter out superusers and delete the remaining users
        User.objects.filter(is_superuser=False).delete()
        # Step 2: Delete all league groups
        self.stdout.write("Deleting all league groups...")
        LeagueGroup.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All league groups deleted."))

        # Step 3: Reset users' leagues
        self.stdout.write("Resetting users' league information...")
        CustomUser.objects.update(current_league="", exp_this_league=0)
        self.stdout.write(self.style.SUCCESS("Users' league information reset."))
