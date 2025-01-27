# Generated by Django 5.1.2 on 2024-12-17 16:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='League',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('icon', models.CharField(max_length=255)),
                ('order', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='LeagueGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_start', models.DateField()),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leaderboards.league')),
            ],
        ),
        migrations.CreateModel(
            name='UserLeaguePlacement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exp_earned', models.IntegerField(default=0)),
                ('league_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leaderboards.leaguegroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'league_group')},
            },
        ),
        migrations.AddField(
            model_name='leaguegroup',
            name='users',
            field=models.ManyToManyField(through='leaderboards.UserLeaguePlacement', to=settings.AUTH_USER_MODEL),
        ),
    ]
