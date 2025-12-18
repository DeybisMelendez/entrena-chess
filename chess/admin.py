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
    RetryPuzzle,
)

User = get_user_model()


@admin.register(TrainingPreferences)
class TrainingPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "puzzles_per_cycle")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "lichess_name", "is_trainable")
    search_fields = ("name", "lichess_name", "is_trainable")
    ordering = ("name",)


class TrainingCycleThemeInline(admin.TabularInline):
    model = TrainingCycleTheme
    extra = 0
    readonly_fields = ("theme", "priority")
    autocomplete_fields = ("theme",)


@admin.register(TrainingCycle)
class TrainingCycleAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "start_date",
        "end_date",
        "total_puzzles",
        "completed_puzzles",
        "created_at",
    )
    list_filter = ("start_date", "end_date")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)
    date_hierarchy = "start_date"

    inlines = [TrainingCycleThemeInline]


@admin.register(TrainingCycleTheme)
class TrainingCycleThemeAdmin(admin.ModelAdmin):
    list_display = ("cycle", "theme", "priority")
    list_filter = ("priority", "theme")
    search_fields = (
        "cycle__user__username",
        "cycle__user__email",
        "theme__name",
    )
    autocomplete_fields = ("cycle", "theme")
    list_select_related = ("cycle", "theme")


@admin.register(Elo)
class EloAdmin(admin.ModelAdmin):
    list_display = ("user", "elo", "puzzles_played", "last_updated")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("last_updated",)
    autocomplete_fields = ("user",)


@admin.register(ThemeElo)
class ThemeEloAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "elo", "puzzles_played", "last_updated")
    list_filter = ("theme",)
    search_fields = ("user__username", "user__email", "theme__name")
    readonly_fields = ("last_updated",)
    autocomplete_fields = ("user", "theme")
    list_select_related = ("user", "theme")


@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "solved", "failed")
    list_filter = ("date",)
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user",)
    date_hierarchy = "date"


@admin.register(PuzzleAttempt)
class PuzzleAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "puzzle_id",
        "theme",
        "solved",
        "created_at",
    )
    list_filter = ("solved", "theme", "created_at")
    search_fields = ("user__username", "puzzle_id")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user", "theme")
    date_hierarchy = "created_at"
    list_select_related = ("user", "theme")


@admin.register(ActiveExercise)
class ActiveExerciseAdmin(admin.ModelAdmin):
    list_display = ("user", "puzzle_id", "created_at")
    search_fields = ("user__username", "puzzle_id")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    list_select_related = ("user",)


@admin.register(RetryPuzzle)
class RetryPuzzleAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "puzzle_id",
        "theme",
        "fail_count",
        "last_attempt_at",
    )
    list_filter = ("theme",)
    search_fields = ("user__username", "puzzle_id")
    readonly_fields = ("last_attempt_at",)
    autocomplete_fields = ("user", "theme")
    list_select_related = ("user", "theme")
