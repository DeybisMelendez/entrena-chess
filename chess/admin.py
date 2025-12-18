from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import (
    TrainingPreferences,
    Theme,
    TrainingCycle,
    TrainingCycleTheme,
    Elo,
    ThemeElo,
    DailyProgress,
    PuzzleAttempt,
    ActiveExercise,
    PuzzleTraining,
    TrainingStreak,
)

User = get_user_model()


@admin.register(TrainingPreferences)
class TrainingPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "puzzles_per_cycle", "time_limit_seconds")
    search_fields = ("user__username", "user__email")


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "lichess_name")
    search_fields = ("name", "lichess_name")


class TrainingCycleThemeInline(admin.TabularInline):
    model = TrainingCycleTheme
    extra = 0
    readonly_fields = ("theme", "priority")


@admin.register(TrainingCycle)
class TrainingCycleAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "start_date",
        "end_date",
        "total_exercises",
        "completed_exercises",
        "created_at",
    )
    list_filter = ("start_date", "end_date")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)

    inlines = [TrainingCycleThemeInline]


@admin.register(TrainingCycleTheme)
class TrainingCycleThemeAdmin(admin.ModelAdmin):
    list_display = (
        "cycle",
        "theme",
        "priority",
    )
    list_filter = (
        "priority",
        "theme",
    )
    search_fields = (
        "cycle__user__username",
        "cycle__user__email",
        "theme__name",
    )


@admin.register(Elo)
class EloAdmin(admin.ModelAdmin):
    list_display = ("user", "elo", "puzzles_played", "last_updated")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("last_updated",)


@admin.register(ThemeElo)
class ThemeEloAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "elo", "puzzles_played", "last_updated")
    list_filter = ("theme",)
    search_fields = ("user__username", "user__email", "theme__name")
    readonly_fields = ("last_updated",)


@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "solved", "failed")
    list_filter = ("date",)
    search_fields = ("user__username", "user__email")


@admin.register(PuzzleAttempt)
class PuzzleAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "puzzle_id",
        "theme_origin",
        "solved",
        "time_spent",
        "created_at",
    )
    list_filter = ("solved", "theme_origin", "created_at")
    search_fields = ("user__username", "puzzle_id")
    readonly_fields = ("created_at",)


@admin.register(ActiveExercise)
class ActiveExerciseAdmin(admin.ModelAdmin):
    list_display = ("user", "puzzle_id", "assigned_at")
    search_fields = ("user__username", "puzzle_id")
    readonly_fields = ("assigned_at",)


@admin.register(PuzzleTraining)
class PuzzleTrainingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "puzzle_id",
        "theme_origin",
        "solved",
        "fail_count",
        "last_attempt_at",
    )
    list_filter = ("solved", "theme_origin")
    search_fields = ("user__username", "puzzle_id")
    readonly_fields = ("last_attempt_at",)


@admin.register(TrainingStreak)
class TrainingStreakAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "current_streak",
        "longest_streak",
        "last_training_date",
    )
    search_fields = ("user__username", "user__email")
