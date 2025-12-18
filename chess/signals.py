from .models import (
    Theme,
    ThemeElo,
    TrainingPreferences,
    TrainingCycle,
    TrainingCycleTheme,
    Elo,
)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()


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


@receiver(post_save, sender=User)
def create_user_training_base(sender, instance, created, **kwargs):
    if not created:
        return

    TrainingPreferences.objects.create(user=instance)
    Elo.objects.create(user=instance)

    themes = Theme.objects.all()
    ThemeElo.objects.bulk_create(
        [
            ThemeElo(user=instance, theme=theme)
            for theme in themes
        ]
    )


@receiver(post_save, sender=Theme)
def create_theme_elos_for_all_users(sender, instance, created, **kwargs):
    if not created:
        return

    users = User.objects.all()
    ThemeElo.objects.bulk_create(
        [
            ThemeElo(user=user, theme=instance)
            for user in users
        ],
        ignore_conflicts=True
    )


@receiver(post_save, sender=TrainingCycle)
def assign_cycle_themes(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.themes.exists():
        return

    theme_elos = (
        ThemeElo.objects
        .filter(
            user=instance.user,
            theme__is_trainable=True
        )
        .select_related("theme")
    )

    if not theme_elos.exists():
        return

    weak_themes = theme_elos.order_by("elo")[:2]
    weak_theme_ids = weak_themes.values_list("theme_id", flat=True)

    strong_theme = (
        theme_elos
        .exclude(theme_id__in=weak_theme_ids)
        .order_by("-elo")
        .first()
    )

    with transaction.atomic():
        objs = [
            TrainingCycleTheme(
                cycle=instance,
                theme=theme_elo.theme,
                priority=priority
            )
            for priority, theme_elo in enumerate(weak_themes, start=1)
        ]

        if strong_theme:
            objs.append(
                TrainingCycleTheme(
                    cycle=instance,
                    theme=strong_theme.theme,
                    priority=3
                )
            )

        TrainingCycleTheme.objects.bulk_create(objs)
