# Generated by Django 5.1.4 on 2025-01-03 06:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaderboards', '0003_remove_userleagueplacement_leaderboard_league__757ded_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='league',
            options={'ordering': ['order']},
        ),
        migrations.AlterField(
            model_name='league',
            name='icon',
            field=models.ImageField(upload_to='league_icons/'),
        ),
        migrations.AlterField(
            model_name='league',
            name='order',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='leaguegroup',
            name='league',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='leaderboards.league'),
        ),
        migrations.AlterField(
            model_name='leaguegroup',
            name='users',
            field=models.ManyToManyField(related_name='league_groups', through='leaderboards.UserLeaguePlacement', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userleagueplacement',
            name='league_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placements', to='leaderboards.leaguegroup'),
        ),
        migrations.AlterField(
            model_name='userleagueplacement',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='league_placements', to=settings.AUTH_USER_MODEL),
        ),
    ]
