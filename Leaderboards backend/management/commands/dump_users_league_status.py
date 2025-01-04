# python manage.py dump_users_league_status --filename=after_reset.json
# leaderboards/management/commands/dump_users_league_status.py

import json
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from leaderboards.models import UserLeaguePlacement

class Command(BaseCommand):
    help = "Dump all users and their league status (rank, league, xp) to a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            type=str,
            default='users_league_status.json',
            help='Output JSON filename (default: users_league_status.json)'
        )

    def handle(self, *args, **options):
        filename = options['filename']

        data_output = []
        users = CustomUser.objects.all().order_by("id")
        for user in users:
            # Attempt to find the user’s league placement 
            # (we assume they might only have 1 for the current cycle, or none)
            placement = (
                UserLeaguePlacement.objects.filter(user=user)
                .order_by("-exp_earned")  # or filter by the current cycle
                .first()
            )
            rank = None
            exp_earned = None
            if placement:
                # rank is tricky if we want the rank in that group
                group_placements = list(
                    UserLeaguePlacement.objects.filter(league_group=placement.league_group)
                    .order_by("-exp_earned")
                )
                # find index
                for i, gp in enumerate(group_placements):
                    if gp.user_id == user.id:
                        rank = i + 1
                        exp_earned = gp.exp_earned
                        break

            data_output.append({
                "email": user.email,
                "current_league": user.current_league,
                "exp_this_league": user.exp_this_league,
                "placement_exp_earned": exp_earned,
                "rank_in_group": rank,
            })

        with open(filename, "w") as f:
            json.dump(data_output, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f"Dumped user league status to {filename}"))
