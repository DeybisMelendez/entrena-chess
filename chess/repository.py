import sqlite3
import random
from pathlib import Path
from django.conf import settings


class LichessDB:
    """
    Acceso a la base de datos de puzzles de Lichess (SQLite).

    - Random rápido con rnd precomputado
    - Filtro por rating y theme(s)
    - Devuelve los themes del puzzle seleccionado
    - Lookup directo por puzzle_id
    """

    def __init__(self):
        self.db_path = Path(settings.BASE_DIR) / "lichess_puzzles.sqlite3"

    def connect(self):
        return sqlite3.connect(self.db_path)

    def get_board_orientation(self, fen):
        try:
            return "white" if fen.split()[1] == "b" else "black"
        except Exception:
            return "white"

    # =====================================================
    # Random óptimo por rating + theme(s)
    # =====================================================
    def get_random_puzzle(self, rating_min=0, rating_max=3000, themes=None):
        """
        themes: lista de nombres de themes (al menos uno)
        """
        themes = themes or []

        conn = self.connect()
        cursor = conn.cursor()

        rnd = random.randint(0, 2**31 - 1)

        # ----------------------------
        # Construir JOIN y WHERE
        # ----------------------------
        join = ""
        where = [
            "p.rating BETWEEN ? AND ?",
            "p.rnd >= ?",
        ]
        params = [rating_min, rating_max, rnd]

        if themes:
            join = """
                JOIN puzzle_themes pt ON pt.puzzle_id = p.puzzle_id
                JOIN themes t ON t.id = pt.theme_id
            """
            where.append(
                "t.name IN ({})".format(",".join("?" * len(themes)))
            )
            params.extend(themes)

        where_sql = " AND ".join(where)

        # ----------------------------
        # Query principal
        # ----------------------------
        cursor.execute(f"""
            SELECT DISTINCT
                p.puzzle_id,
                p.fen,
                p.moves,
                p.rating
            FROM puzzles p
            {join}
            WHERE {where_sql}
            ORDER BY p.rnd
            LIMIT 1
        """, params)

        row = cursor.fetchone()

        # ----------------------------
        # Wrap-around
        # ----------------------------
        if not row:
            cursor.execute(f"""
                SELECT DISTINCT
                    p.puzzle_id,
                    p.fen,
                    p.moves,
                    p.rating
                FROM puzzles p
                {join}
                WHERE p.rating BETWEEN ? AND ?
                ORDER BY p.rnd
                LIMIT 1
            """, [rating_min, rating_max] + themes)

            row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        puzzle_id, fen, moves, rating = row

        # ----------------------------
        # Obtener TODOS los themes del puzzle
        # ----------------------------
        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))

        theme_list = [r[0] for r in cursor.fetchall()]
        conn.close()

        return {
            "puzzle_id": puzzle_id,
            "fen": fen,
            "moves": moves.split(),
            "rating": rating,
            "orientation": self.get_board_orientation(fen),
            "themes": theme_list,
        }

    # =====================================================
    # Lookup directo por ID
    # =====================================================
    def get_puzzle_by_id(self, puzzle_id):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT puzzle_id, fen, moves, rating
            FROM puzzles
            WHERE puzzle_id = ?
        """, (puzzle_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        puzzle_id, fen, moves, rating = row

        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))

        theme_list = [r[0] for r in cursor.fetchall()]
        conn.close()

        return {
            "puzzle_id": puzzle_id,
            "fen": fen,
            "moves": moves.split(),
            "rating": rating,
            "orientation": self.get_board_orientation(fen),
            "themes": theme_list,
        }
