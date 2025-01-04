from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.timezone import now, timedelta
from django.conf import settings
from datetime import timedelta
from django.db import models, transaction
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser, allowing email as the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault(
            "username", email.split("@")[0]
        )  # Default username from email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model with additional fields and streak functionality.
    """

    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    gems_count = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    previous_streak = models.IntegerField(default=0)
    hearts_count = models.IntegerField(default=5)
    exp_count = models.IntegerField(default=0)
    amount_of_streak_freezes = models.IntegerField(default=0)
    streak_repairs = models.IntegerField(default=0)
    is_premium = models.BooleanField(default=False)
    friends = models.ManyToManyField("self", blank=True, symmetrical=True)
    current_league = models.CharField(max_length=50, default="")
    joined = models.DateField(default=now)
    last_lesson_date = models.DateTimeField(null=True, blank=True)
    has_done_daily_lesson = models.BooleanField(default=False)
    followers = models.ManyToManyField(
        "self", symmetrical=False, related_name="following", blank=True
    )
    profile_pic_number = models.IntegerField(default=0)
    exp_this_league = models.IntegerField(default=0)
    exp_for_today_spaced_repetition = models.IntegerField(default=0)
    exp_for_today = models.IntegerField(default=0)
    exp_to_enter = models.IntegerField(default=0)
    objects = CustomUserManager()
    correct_questions_today = models.IntegerField(default=0)
    practice_minutes_today = models.IntegerField(default=0)
    lessons_completed_today = models.IntegerField(default=0)
    high_score_lessons = models.IntegerField(default=0)  # For lessons >90%
    medium_score_lessons = models.IntegerField(default=0)  # For lessons >80%

    def __str__(self):
        return self.email

    # Follower methods
    def follow(self, user):
        if user != self:
            self.following.add(user)

    def unfollow(self, user):
        self.following.remove(user)

    def is_following(self, user):
        return self.following.filter(pk=user.pk).exists()

    def is_followed_by(self, user):
        return self.followers.filter(pk=user.pk).exists()

    # Streak methods

    def increment_streak(self):
        """
        Increment the user's streak if they have completed a daily lesson and have not already done so today.
        Reset or freeze the streak if they missed a day.
        """
        with transaction.atomic():
            current_time = timezone.now()
            start_of_today = current_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_of_yesterday = start_of_today - timedelta(days=1)

            if settings.DEBUG:
                print(f"DEBUG: Current time: {current_time}")
                print(f"DEBUG: Start of today: {start_of_today}")
                print(f"DEBUG: Start of yesterday: {start_of_yesterday}")
                print(
                    f"DEBUG: Last lesson date before processing: {self.last_lesson_date}"
                )
                print(f"DEBUG: Streak before processing: {self.streak}")
                print(
                    f"DEBUG: Has done daily lesson before processing: {self.has_done_daily_lesson}"
                )

            # Check if the user has already completed a lesson today
            if self.has_done_daily_lesson:
                if settings.DEBUG:
                    print(
                        "DEBUG: Daily lesson already completed, exiting increment_streak."
                    )
                return  # Exit early to prevent multiple increments per day

            if self.streak == 0:
                self.streak = 1  # Initialize streak if it's 0
                if settings.DEBUG:
                    print("DEBUG: Initial streak set to 1.")

            # If the user has a last lesson date
            if self.last_lesson_date:
                if self.last_lesson_date >= start_of_today:
                    # Lesson already completed today (shouldn't happen due to has_done_daily_lesson check)
                    if settings.DEBUG:
                        print(
                            "DEBUG: Lesson already marked as done today, marking daily lesson as done."
                        )
                    self.has_done_daily_lesson = True
                elif start_of_yesterday <= self.last_lesson_date < start_of_today:
                    # Lesson was completed yesterday, increment streak
                    if self.streak == 0:
                        self.streak = 1  # Initialize streak if it's 0
                        if settings.DEBUG:
                            print("DEBUG: Initial streak set to 1.")
                    else:
                        self.streak += 1  # Increment existing streak
                        if settings.DEBUG:
                            print("DEBUG: Streak incremented by 1.")
                    self.has_done_daily_lesson = True
                else:
                    # Missed one or more days
                    if settings.DEBUG:
                        print(
                            "DEBUG: Last lesson was before yesterday, handling missed day(s)."
                        )
                    self._handle_missed_day()
            else:
                # No last lesson date implies first lesson
                self.streak = 1
                self.has_done_daily_lesson = True
                if settings.DEBUG:
                    print("DEBUG: First lesson detected, initializing streak to 1.")

            # Update last_lesson_date to current_time
            self.last_lesson_date = current_time

            if settings.DEBUG:
                print(f"DEBUG: Streak after processing: {self.streak}")
                print(
                    f"DEBUG: Last lesson date after processing: {self.last_lesson_date}"
                )

            self.save()

    def _handle_missed_day(self):
        """
        Handles streak behavior when a day is missed, including applying streak freezes.
        Assumes this method is called within an atomic transaction.
        """
        if settings.DEBUG:
            print("DEBUG: Handling missed day.")
            print(
                f"DEBUG: Amount of streak freezes before processing: {self.amount_of_streak_freezes}"
            )
            print(f"DEBUG: Streak before handling missed day: {self.streak}")

        if self.amount_of_streak_freezes > 0:
            # Use a streak freeze to maintain the streak
            self.amount_of_streak_freezes -= 1
            if settings.DEBUG:
                print("DEBUG: Using a streak freeze. Streak remains unchanged.")
            # Streak remains the same
        else:
            # No streak freezes left, reset the streak
            self.previous_streak = self.streak  # Backup current streak
            self.streak = 1  # Reset streak to 1 since the user is completing today
            if settings.DEBUG:
                print("DEBUG: No streak freezes left, resetting streak to 1.")

        self.has_done_daily_lesson = False  # Reset daily lesson status

        if settings.DEBUG:
            print(
                f"DEBUG: Has done daily lesson after handling missed day: {self.has_done_daily_lesson}"
            )

    def use_streak_repair(self):
        """
        Use a streak repair to restore the previous streak.
        This method is atomic to prevent race conditions.
        """
        with transaction.atomic():
            if settings.DEBUG:
                print("DEBUG: Attempting to use streak repair.")
                print(
                    f"DEBUG: Streak repairs available before use: {self.streak_repairs}"
                )
                print(f"DEBUG: Previous streak: {self.previous_streak}")

            if self.streak_repairs > 0:
                self.streak_repairs -= 1
                self.streak = self.previous_streak  # Restore streak
                self.previous_streak = 1  # Clear backup streak after repair
                self.save()
                if settings.DEBUG:
                    print("DEBUG: Streak repair successful.")
                    print(f"DEBUG: Streak after repair: {self.streak}")
                return True
            if settings.DEBUG:
                print("DEBUG: Streak repair failed - no repairs available.")
            return False

    def update_profile_pic_number(self):
        """
        Updates the user's profile_pic_number based on their exp_count.
        Each 10k exp upgrades to the next picture, capped at 10.
        This method is atomic to prevent race conditions.
        """
        with transaction.atomic():
            if settings.DEBUG:
                print("DEBUG: Updating profile picture number.")
                print(f"DEBUG: EXP count: {self.exp_count}")
                print(
                    f"DEBUG: Profile picture number before update: {self.profile_pic_number}"
                )
            self.profile_pic_number = min(self.exp_count // 10000, 10)
            self.save()
            if settings.DEBUG:
                print(
                    f"DEBUG: Profile picture number after update: {self.profile_pic_number}"
                )
