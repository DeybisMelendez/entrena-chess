from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .models import (
    TrainingPreferences,
    Theme,
    ThemeElo,
)


@receiver(post_save, sender=TrainingPreferences)
def create_theme_elos_for_user(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    themes = Theme.objects.all()

    if not themes.exists():
        return

    theme_elos = [
        ThemeElo(user=user, theme=theme)
        for theme in themes
    ]

    with transaction.atomic():
        ThemeElo.objects.bulk_create(
            theme_elos,
            ignore_conflicts=True
        )


@receiver(post_save, sender=Theme)
def create_theme_elos_for_theme(sender, instance, created, **kwargs):
    if not created:
        return

    theme = instance
    preferences = TrainingPreferences.objects.select_related("user")

    theme_elos = [
        ThemeElo(user=pref.user, theme=theme)
        for pref in preferences
    ]

    if not theme_elos:
        return

    with transaction.atomic():
        ThemeElo.objects.bulk_create(
            theme_elos,
            ignore_conflicts=True
        )
