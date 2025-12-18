import sqlite3
from pathlib import Path
from django.conf import settings


class LichessDB:
    """
    Pequeña librería para acceder a la base de datos de puzzles de Lichess.
    Maneja conexiones, consultas y modelos simples.
    """

    def __init__(self):
        # Ruta absoluta a la base de datos
        self.db_path = Path(settings.BASE_DIR) / "lichess_puzzles.sqlite3"

    def connect(self):
        """Crea una conexión nueva."""
        return sqlite3.connect(self.db_path)

    # ---------------------------------------------------------------------
    # UTILITIES
    # ---------------------------------------------------------------------

    def get_board_orientation(self, fen):
        """Determina la orientación del tablero según el FEN."""
        # Debido a que el rival juega primero, la orientación es opuesta al color
        # que tiene el turno en el FEN.
        try:
            return "white" if fen.split()[1] == "b" else "black"
        except Exception:
            return "white"

    # ---------------------------------------------------------------------
    # QUERY PRINCIPAL: obtener puzzle aleatorio con filtros
    # ---------------------------------------------------------------------

    def get_random_puzzle(self, rating_min=0, rating_max=3000, themes=None, openings=None):
        """
        Obtiene un puzzle aleatorio usando filtros.
        themes y openings deben ser listas de strings o None.
        """
        themes = themes or []
        openings = openings or []

        conn = self.connect()
        cursor = conn.cursor()

        # Base del query
        query = """
            SELECT DISTINCT p.puzzle_id, p.fen, p.moves, p.rating
            FROM puzzles p
        """

        # JOINs condicionales
        if themes:
            query += """
                JOIN puzzle_themes pt ON pt.puzzle_id = p.puzzle_id
                JOIN themes t ON t.id = pt.theme_id
            """

        if openings:
            query += """
                JOIN puzzle_openings po ON po.puzzle_id = p.puzzle_id
                JOIN openings o ON o.id = po.opening_id
            """

        # WHERE base
        query += " WHERE p.rating BETWEEN ? AND ? "
        params = [rating_min, rating_max]

        # Filtros por temas
        if themes:
            query += " AND t.name IN (" + ",".join("?" * len(themes)) + ")"
            params.extend(themes)

        # Filtros por aperturas
        if openings:
            query += " AND o.name IN (" + ",".join("?" * len(openings)) + ")"
            params.extend(openings)

        query += " ORDER BY RANDOM() LIMIT 1"

        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        puzzle_id = row[0]

        # Obtener temas del puzzle
        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))
        theme_list = [x[0] for x in cursor.fetchall()]

        # Obtener aperturas del puzzle
        cursor.execute("""
            SELECT o.name
            FROM openings o
            JOIN puzzle_openings po ON po.opening_id = o.id
            WHERE po.puzzle_id = ?
        """, (puzzle_id,))
        opening_list = [x[0] for x in cursor.fetchall()]

        conn.close()

        # Crear estructura limpia tipo "modelo"
        return {
            "puzzle_id": row[0],
            "fen": row[1],
            "moves": row[2].split(),
            "rating": row[3],
            "orientation": self.get_board_orientation(row[1]),
            "themes": theme_list,
            "openings": opening_list,
        }

    def get_puzzle_by_id(self, puzzle_id):
        """
        Obtiene un puzzle específico por su puzzle_id.
        Devuelve la misma estructura que get_random_puzzle.
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Obtener datos principales del puzzle
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

        # Obtener temas del puzzle
        cursor.execute("""
            SELECT t.name
            FROM themes t
            JOIN puzzle_themes pt ON pt.theme_id = t.id
            WHERE pt.puzzle_id = ?
        """, (puzzle_id,))
        theme_list = [x[0] for x in cursor.fetchall()]

        # Obtener aperturas del puzzle
        cursor.execute("""
            SELECT o.name
            FROM openings o
            JOIN puzzle_openings po ON po.opening_id = o.id
            WHERE po.puzzle_id = ?
        """, (puzzle_id,))
        opening_list = [x[0] for x in cursor.fetchall()]

        conn.close()

        return {
            "puzzle_id": row[0],
            "fen": row[1],
            "moves": row[2].split(),
            "rating": row[3],
            "orientation": self.get_board_orientation(row[1]),
            "themes": theme_list,
            "openings": opening_list,
        }

    def get_puzzle_themes(self, puzzle_id):
        """
        Retorna la lista de nombres de temas asociados a un puzzle_id.
        """
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

    # ---------------------------------------------------------------------
    # CONSULTAS AUXILIARES
    # ---------------------------------------------------------------------

    def get_all_themes(self):
        """Retorna lista de temas disponibles."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM themes ORDER BY name ASC")
        data = [x[0] for x in cursor.fetchall()]
        conn.close()
        return data

    def get_all_openings(self):
        """Retorna lista de aperturas disponibles."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM openings ORDER BY name ASC")
        data = [x[0] for x in cursor.fetchall()]
        conn.close()
        return data
