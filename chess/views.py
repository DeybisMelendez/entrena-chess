import sqlite3
import random
from django.http import JsonResponse
from django.conf import settings
from pathlib import Path
from django.shortcuts import render

def get_puzzle(request):
    theme = request.GET.get("theme", "")
    rating_min = int(request.GET.get("ratingMin", "0"))
    rating_max = int(request.GET.get("ratingMax", "3000"))

    db_path = Path(settings.BASE_DIR) / "lichess_puzzles.sqlite3"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT puzzle_id, fen, moves, rating, themes, opening_tags
        FROM puzzles
        WHERE rating BETWEEN ? AND ?
    """
    params = [rating_min, rating_max]

    if theme:
        query += " AND themes LIKE ?"
        params.append(f"%{theme}%")

    query += " ORDER BY RANDOM() LIMIT 1"

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return HttpResponse("<p>No puzzle found</p>")

    puzzle = {
        "puzzle_id": row[0],
        "fen": row[1],
        "moves": row[2].split(),
        "rating": row[3],
        "themes": row[4].split(),
        "opening_tags": row[5].split() if row[5] else []
    }

    return render(request, "htmx/puzzle.html", {"puzzle": puzzle})


def watch_puzzle(request):
    return render(request, "prueba.html")