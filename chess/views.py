import sqlite3
import random
from django.http import JsonResponse
from django.conf import settings
from pathlib import Path
from django.shortcuts import render
from .repository import LichessDB

def get_puzzle(request):
    db = LichessDB()

    theme = request.GET.get("theme", "")
    opening = request.GET.get("opening", "")

    themes = theme.split(",") if theme else None
    openings = opening.split(",") if opening else None

    puzzle = db.get_random_puzzle(
        rating_min=int(request.GET.get("ratingMin", 0)),
        rating_max=int(request.GET.get("ratingMax", 3000)),
        themes=themes,
        openings=openings,
    )

    if not puzzle:
        return HttpResponse("<p>No puzzle found</p>")

    return render(request, "htmx/puzzle.html", {"puzzle": puzzle})


def watch_puzzle(request):
    return render(request, "prueba.html")