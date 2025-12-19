import sqlite3
from pathlib import Path
from django.conf import settings
import random


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
        """
        themes = themes or []

        conn = self.connect()
        cursor = conn.cursor()

        # ----------------------------
        # 1. Construir WHERE y JOIN
        # ----------------------------
        where = ["p.rating BETWEEN ? AND ?"]
        params = [rating_min, rating_max]

        join = ""
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
        # 2. Contar candidatos
        # ----------------------------
        cursor.execute(f"""
            SELECT COUNT(DISTINCT p.puzzle_id)
            FROM puzzles p
            {join}
            WHERE {where_sql}
        """, params)

        total = cursor.fetchone()[0]
        if total == 0:
            conn.close()
            return None

        offset = random.randint(0, total - 1)

        # ----------------------------
        # 3. Obtener puzzle por OFFSET
        # ----------------------------
        cursor.execute(f"""
            SELECT DISTINCT p.puzzle_id, p.fen, p.moves, p.rating
            FROM puzzles p
            {join}
            WHERE {where_sql}
            LIMIT 1 OFFSET ?
        """, params + [offset])

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        puzzle_id, fen, moves, rating = row

        # ----------------------------
        # 4. Obtener themes del puzzle
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

        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))

        theme_list = [r[0] for r in cursor.fetchall()]
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
