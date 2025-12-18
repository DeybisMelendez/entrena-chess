import sqlite3
from pathlib import Path
from django.conf import settings


class LichessDB:
    """
    Acceso a la base de datos de puzzles de Lichess (SQLite).
    Todos los tags (tácticas, fases, aperturas) se manejan como THEMES.
    """

    def __init__(self):
        self.db_path = Path(settings.BASE_DIR) / "lichess_puzzles.sqlite3"

    def connect(self):
        return sqlite3.connect(self.db_path)

    def get_board_orientation(self, fen):
        """Determina la orientación del tablero según el FEN."""
        try:
            return "white" if fen.split()[1] == "b" else "black"
        except Exception:
            return "white"

    def get_random_puzzle(self, rating_min=0, rating_max=3000, themes=None):
        """
        Obtiene un puzzle aleatorio filtrado por rating y themes.

        themes: lista de strings (tags de lichess, tácticas o aperturas)
        """
        themes = themes or []

        conn = self.connect()
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT p.puzzle_id, p.fen, p.moves, p.rating
            FROM puzzles p
        """

        if themes:
            query += """
                JOIN puzzle_themes pt ON pt.puzzle_id = p.puzzle_id
                JOIN themes t ON t.id = pt.theme_id
            """

        query += " WHERE p.rating BETWEEN ? AND ? "
        params = [rating_min, rating_max]

        if themes:
            query += " AND t.name IN (" + ",".join("?" * len(themes)) + ")"
            params.extend(themes)

        query += " ORDER BY RANDOM() LIMIT 1"

        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        puzzle_id = row[0]

        # Obtener themes del puzzle
        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))

        theme_list = [x[0] for x in cursor.fetchall()]

        conn.close()

        return {
            "puzzle_id": row[0],
            "fen": row[1],
            "moves": row[2].split(),
            "rating": row[3],
            "orientation": self.get_board_orientation(row[1]),
            "themes": theme_list,
        }

    def get_puzzle_by_id(self, puzzle_id):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT puzzle_id, fen, moves, rating
            FROM puzzles
            WHERE puzzle_id = ?
            LIMIT 1
        """, (puzzle_id,))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))

        theme_list = [x[0] for x in cursor.fetchall()]

        conn.close()

        return {
            "puzzle_id": row[0],
            "fen": row[1],
            "moves": row[2].split(),
            "rating": row[3],
            "orientation": self.get_board_orientation(row[1]),
            "themes": theme_list,
        }

    def get_puzzle_themes(self, puzzle_id):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))

        themes = [row[0] for row in cursor.fetchall()]
        conn.close()
        return themes

    def get_all_themes(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM themes ORDER BY name ASC")
        data = [x[0] for x in cursor.fetchall()]
        conn.close()
        return data
