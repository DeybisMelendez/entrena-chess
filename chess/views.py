from datetime import date
import json
import random
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.timezone import make_aware
from datetime import datetime
from django.db.models import Count, Q
from django.db.models import Prefetch
from .models import (
    TrainingPreferences,
    TrainingCycle,
    TrainingCycleTheme,
    ThemeElo,
    PuzzleAttempt,
    ActiveExercise,
    RetryPuzzle,
    Elo,
    Theme,
)
from .utils import get_week_cycle_dates, pick_cycle_theme
from .repository import LichessDB


@login_required
def get_puzzle(request):
    user = request.user
    today = date.today()
    db = LichessDB()

    preferences = TrainingPreferences.objects.get(user=user)
    start_date, end_date = get_week_cycle_dates(today)

    cycle, _ = TrainingCycle.objects.get_or_create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        defaults={
            "total_puzzles": preferences.puzzles_per_cycle,
        }
    )

    cycle_themes = cycle.themes.select_related("theme")
    if not cycle_themes.exists():
        raise Http404("El ciclo no tiene temas asignados.")

    active = ActiveExercise.objects.filter(user=user).first()
    if active:
        puzzle = db.get_puzzle_by_id(active.puzzle_id)
        if not puzzle:
            active.delete()
            raise Http404("Puzzle activo inválido.")
        return render(
            request,
            "puzzle.html",
            {
                "puzzle": puzzle,
                "cycle": cycle,
                "themes": cycle_themes,
            }
        )

    retry_qs = RetryPuzzle.objects.filter(
        user=user
    ).order_by("-fail_count", "last_attempt_at")

    if retry_qs.exists() and random.random() < 0.1:
        retry = retry_qs.first()
        puzzle = db.get_puzzle_by_id(retry.puzzle_id)
    else:
        cycle_theme = pick_cycle_theme(cycle_themes)
        theme = cycle_theme.theme

        theme_elo = ThemeElo.objects.get(user=user, theme=theme)

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

    return render(
        request,
        "puzzle.html",
        {
            "puzzle": puzzle,
            "cycle": cycle,
            "themes": cycle_themes,
        }
    )


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
        return JsonResponse(
            {"status": "error", "message": "Puzzle activo inválido"},
            status=400,
        )

    active.delete()

    PuzzleAttempt.objects.create(
        user=user,
        puzzle_id=puzzle_id,
        solved=solved,
    )

    if solved:
        RetryPuzzle.objects.filter(
            user=user,
            puzzle_id=puzzle_id,
        ).delete()
    else:
        retry, _ = RetryPuzzle.objects.get_or_create(
            user=user,
            puzzle_id=puzzle_id,
        )
        retry.fail_count += 1
        retry.save(update_fields=["fail_count", "last_attempt_at"])

    cycle = TrainingCycle.objects.filter(
        user=user,
        start_date__lte=today,
        end_date__gte=today,
    ).first()

    if solved and cycle:
        cycle.completed_puzzles += 1
        cycle.save(update_fields=["completed_puzzles"])

    db = LichessDB()
    puzzle_data = db.get_puzzle_by_id(puzzle_id)

    puzzle_rating = puzzle_data["rating"]
    puzzle_themes = puzzle_data["themes"]
    score = 1.0 if solved else 0.0

    elo_changes = []

    user_elo = Elo.objects.get(user=user)
    old_general = user_elo.elo

    user_elo.update_elo(
        opponent_elo=puzzle_rating,
        score=score,
    )

    elo_changes.append({
        "name": "General",
        "old": old_general,
        "new": user_elo.elo,
    })

    themes = set()

    for theme_name in puzzle_themes:
        try:
            theme = Theme.objects.get(lichess_name=theme_name)
        except Theme.DoesNotExist:
            continue

        themes.add(theme)

    for theme in themes:
        theme_elo, _ = ThemeElo.objects.get_or_create(
            user=user,
            theme=theme,
        )

        old_elo = theme_elo.elo

        theme_elo.update_elo(
            opponent_elo=puzzle_rating,
            score=score,
        )

        elo_changes.append({
            "name": theme.name,
            "old": old_elo,
            "new": theme_elo.elo,
        })

    return JsonResponse(
        {
            "status": "ok",
            "solved": solved,
            "elo_changes": elo_changes,
        }
    )


@login_required
def home(request):
    user = request.user
    today = date.today()

    preferences = TrainingPreferences.objects.get(user=user)
    start_date, end_date = get_week_cycle_dates(today)

    cycle, _ = TrainingCycle.objects.get_or_create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        defaults={
            "total_puzzles": preferences.puzzles_per_cycle,
        }
    )

    user_elo = Elo.objects.get(user=user)

    cycle_themes = TrainingCycleTheme.objects.filter(cycle=cycle)
    opening_elo = ThemeElo.objects.get(
        user=user, theme__lichess_name="opening")
    middlegame_elo = ThemeElo.objects.get(
        user=user, theme__lichess_name="middlegame")
    endgame_elo = ThemeElo.objects.get(
        user=user, theme__lichess_name="endgame")
    mate_elo = ThemeElo.objects.get(
        user=user, theme__lichess_name="mate")

    context = {
        "cycle": cycle,
        "elo": user_elo,
        "opening": opening_elo,
        "middlegame": middlegame_elo,
        "endgame": endgame_elo,
        "mate": mate_elo,
        "cycle_themes": cycle_themes,
    }

    return render(request, "home.html", context)


@login_required
def puzzle_history(request):
    user = request.user

    cycles = (
        TrainingCycle.objects
        .filter(user=user)
        .order_by("-start_date")
    )

    selected_cycle_id = request.GET.get("cycle")
    selected_cycle = None
    attempts = []

    if selected_cycle_id:
        selected_cycle = get_object_or_404(
            TrainingCycle,
            id=selected_cycle_id,
            user=user
        )

        start_dt = make_aware(
            datetime.combine(selected_cycle.start_date, datetime.min.time())
        )
        end_dt = make_aware(
            datetime.combine(selected_cycle.end_date, datetime.max.time())
        )

        attempts = (
            PuzzleAttempt.objects
            .filter(
                user=user,
                created_at__range=(start_dt, end_dt)
            )
            .order_by("-created_at")
        )

    context = {
        "cycles": cycles,
        "selected_cycle": selected_cycle,
        "attempts": attempts,
    }

    return render(request, "puzzle_history.html", context)


@login_required
def theme_overview(request):
    user = request.user

    user_theme_elos = ThemeElo.objects.filter(user=user)

    categories = (
        Theme.objects
        .filter(parent__isnull=True)
        .prefetch_related(
            # Elo de la categoría
            Prefetch(
                "themeelo_set",
                queryset=user_theme_elos,
                to_attr="category_elo"
            ),
            # Subtemas entrenables + su Elo
            Prefetch(
                "subthemes",
                queryset=Theme.objects.filter(is_trainable=True)
                .prefetch_related(
                    Prefetch(
                        "themeelo_set",
                        queryset=user_theme_elos,
                        to_attr="theme_elo"
                    )
                ),
                to_attr="trainable_subthemes"
            )
        )
        .order_by("name")
    )

    return render(
        request,
        "theme_overview.html",
        {"categories": categories}
    )
