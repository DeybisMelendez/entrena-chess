from .models import (
    TrainingPreferences,
    TrainingCycle,
    TrainingCycleTheme,
    ThemeElo,
    DailyProgress,
    PuzzleAttempt,
    ActiveExercise,
    PuzzleTraining,
    Elo,
    Theme
)
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .utils import get_week_cycle_dates, pick_cycle_theme
import sqlite3
import random
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.conf import settings
from pathlib import Path
from django.shortcuts import render
from .repository import LichessDB
from django.views.decorators.http import require_POST
import json


@login_required
def get_puzzle(request):
    db = LichessDB()
    user = request.user
    today = date.today()

    preferences = TrainingPreferences.objects.get(user=user)

    start_date, end_date = get_week_cycle_dates(today)

    cycle, _ = TrainingCycle.objects.get_or_create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        defaults={
            "total": preferences.puzzles_per_cycle,
        }
    )

    cycle_themes = TrainingCycleTheme.objects.filter(cycle=cycle)

    if not cycle_themes.exists():
        raise Http404("El ciclo no tiene temas configurados.")

    active = ActiveExercise.objects.filter(user=user).first()
    if active:
        puzzle = db.get_puzzle_by_id(active.puzzle_id)
        if not puzzle:
            active.delete()
            raise Http404("Puzzle activo inválido.")
        return render(request, "puzzle.html", {"puzzle": puzzle, "cycle": cycle, "themes": cycle_themes})

    puzzles_pending = PuzzleTraining.objects.filter(user=user, solved=False)

    if puzzles_pending.exists() and random.random() < 0.1:
        failed = puzzles_pending.order_by(
            "-fail_count", "last_attempt_at"
        ).first()

        puzzle = db.get_puzzle_by_id(failed.puzzle_id)

    else:

        cycle_theme = pick_cycle_theme(cycle_themes)
        theme = cycle_theme.theme

        theme_elo, _ = ThemeElo.objects.get_or_create(user=user, theme=theme)

        rating_min = max(0, theme_elo.elo - 50)
        rating_max = theme_elo.elo + 50

        puzzle = db.get_random_puzzle(
            rating_min=rating_min,
            rating_max=rating_max,
            themes=[theme.lichess_name],
        )

    if not puzzle:
        raise Http404("No se pudo obtener un puzzle.")

    ActiveExercise.objects.create(
        user=user,
        puzzle_id=puzzle["puzzle_id"],
    )

    return render(request, "puzzle.html", {"puzzle": puzzle, "cycle": cycle, "themes": cycle_themes})


@login_required
@require_POST
def submit_puzzle(request):
    user = request.user
    today = date.today()
    data = json.loads(request.body)

    puzzle_id = data.get("puzzle_id")
    solved = bool(data.get("solved"))

    active = ActiveExercise.objects.filter(user=user).first()

    if not active or active.puzzle_id != puzzle_id:
        return JsonResponse({
            "status": "error",
            "message": "No hay puzzle activo válido"
        }, status=400)

    active.delete()

    PuzzleAttempt.objects.create(
        user=user,
        puzzle_id=puzzle_id,
        solved=solved,
    )
    daily_progress, _ = DailyProgress.objects.get_or_create(
        user=user, date=today)
    if solved:
        training = PuzzleTraining.objects.filter(
            user=user,
            puzzle_id=puzzle_id
        )
        if training.exists():
            training = training.first()
            training.solved = True
            training.save()
        daily_progress.solved += 1
    else:
        training, _ = PuzzleTraining.objects.get_or_create(
            user=user,
            puzzle_id=puzzle_id,
        )
        training.fail_count += 1
        training.solved = False
        training.save()

        daily_progress.failed += 1

    daily_progress.save()

    cycle = TrainingCycle.objects.filter(
        user=user,
        start_date__lte=today,
        end_date__gte=today,
    ).first()

    if solved:
        cycle.completed += 1
        cycle.save()

    db = LichessDB()
    puzzle_data = db.get_puzzle_by_id(puzzle_id)
    puzzle_rating = puzzle_data["rating"]
    puzzle_themes = puzzle_data["themes"]

    score = 1.0 if solved else 0.0

    elo, _ = Elo.objects.get_or_create(user=user)
    elo.update_elo(
        opponent_elo=puzzle_rating,
        score=score
    )

    for theme_name in puzzle_themes:
        try:
            theme = Theme.objects.get(lichess_name=theme_name)
        except Theme.DoesNotExist:
            continue

        theme_elo, _ = ThemeElo.objects.get_or_create(
            user=user,
            theme=theme
        )
        theme_elo.update_elo(
            opponent_elo=puzzle_rating,
            score=score
        )

    return JsonResponse({
        "status": "ok",
        "solved": solved,
    })


def watch_puzzle(request):
    return render(request, "prueba.html")


@login_required
def home(request):
    user = request.user
    today = date.today()

    preferences, _ = TrainingPreferences.objects.get_or_create(
        user=user
    )

    start_date, end_date = get_week_cycle_dates(today)

    cycle, _ = TrainingCycle.objects.get_or_create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        defaults={
            "total": preferences.puzzles_per_cycle,
        }
    )

    today_progress, _ = DailyProgress.objects.get_or_create(
        user=user,
        date=today
    )

    week_progress = DailyProgress.objects.filter(
        user=user,
        date__range=(start_date, end_date)
    ).aggregate(
        solved=Sum("solved"),
        failed=Sum("failed"),
    )

    elo_user, _ = Elo.objects.get_or_create(user=user)

    weak_themes = (
        ThemeElo.objects
        .filter(user=user)
        .select_related("theme")
        .order_by("elo")[:5]
    )

    context = {
        "cycle": cycle,
        "today": today_progress,
        "week": week_progress,
        "elo": elo_user,
        "weak_themes": weak_themes,
    }

    return render(request, "home.html", context)
