# leaderboards/models.py

from django.db import models
from django.conf import settings

# Fixed set of leagues with their icons
LEAGUES = [
    ("Bronze", "images/bronze.png"),
    ("Silver", "images/silver.png"),
    ("Gold", "images/gold.png"),
    ("Platinum", "images/platinum.png"),
    ("Diamond", "images/diamond.png"),
    ("Sapphire", "images/sapphire.png"),
    ("Ruby", "images/ruby.png"),
    ("Emerald", "images/emerald.png"),
    ("Onyx", "images/onyx.png"),
    ("Obsidian", "images/obsidian.png"),
]


class League(models.Model):
    """
    Represents a league type (e.g., Bronze, Silver, etc.).
    This is the definition of a league level.
    """

    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='league_icons/')  # Handles image uploads
    order = models.PositiveIntegerField()  # 0 for Bronze, 1 for Silver, etc.

    class Meta:
        ordering = ['order']  # Orders leagues by 'order' field

    def __str__(self):
        return self.name


class LeagueGroup(models.Model):
    """
    Represents a specific instance of a league (a "room" of up to 30 users).
    Multiple groups of the same league level may exist (e.g., 2 Emerald groups if >30 users).
    """

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='groups')
    week_start = models.DateField()
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="UserLeaguePlacement", related_name='league_groups'
    )

    def __str__(self):
        return f"{self.league.name} group starting {self.week_start}"


class UserLeaguePlacement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='league_placements')
    league_group = models.ForeignKey(LeagueGroup, on_delete=models.CASCADE, related_name='placements')
    exp_earned = models.IntegerField(default=0)  # Experience earned this league period

    class Meta:
        unique_together = ("user", "league_group")

    def __str__(self):
        return f"{self.user.username} in {self.league_group.league.name} with {self.exp_earned} exp"


class UserWeeklyOutcome(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    finished_rank = models.PositiveIntegerField(default=0)
    old_league = models.CharField(max_length=50, blank=True, default="")
    new_league = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} outcome {self.created_at}"