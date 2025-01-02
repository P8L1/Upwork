# leaderboards/models.py

from django.db import models
from django.conf import settings

# We have a fixed set of leagues:
LEAGUES = [
    ("Bronze Calculators", "images/bronze.png"),
    ("Silver Integrals", "images/silver.png"),
    ("Gold Derivatives", "images/gold.png"),
    ("Platinum Limits", "images/platinum.png"),
    ("Diamond Functions", "images/diamond.png"),
    ("Sapphire Gradients", "images/sapphire.png"),
    ("Ruby Series", "images/ruby.png"),
    ("Emerald Tangents", "images/emerald.png"),
    ("Onyx Infinites", "images/onyx.png"),
    ("Obsidian Theorems", "images/obsidian.png"),
]


class League(models.Model):
    """
    Represents a league type (e.g. Bronze, Silver, etc.).
    This is not an instance with users, but the definition of a league level.
    """

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=255)  # path to icon image
    order = models.IntegerField()  # 0 for Bronze, 1 for Silver, etc.

    def __str__(self):
        return self.name


class LeagueGroup(models.Model):
    """
    Represents a specific instance of a league (like one "room" of up to 30 users).
    Multiple groups of the same league level may exist (e.g. 2 Emerald groups if >30 users).
    """

    league = models.ForeignKey(League, on_delete=models.CASCADE)
    week_start = models.DateField()
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="UserLeaguePlacement"
    )

    def __str__(self):
        return f"{self.league.name} group starting {self.week_start}"


class UserLeaguePlacement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    league_group = models.ForeignKey(LeagueGroup, on_delete=models.CASCADE)
    exp_earned = models.IntegerField(default=0)  # exp this league period

    class Meta:
        unique_together = ("user", "league_group")

    def __str__(self):
        return f"{self.user.username} in {self.league_group.league.name} with {self.exp_earned} exp"
