import csv
import sqlite3
from pathlib import Path

# ----- CONFIG -----
CSV_FILE = "lichess_db_puzzle.csv"
SQLITE_FILE = "lichess_puzzles.sqlite3"
rating_deviation_threshold = 76
BATCH_SIZE = 5000
# -------------------

def create_tables(cursor):
    # Crear tablas principales y tablas puente
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS puzzles (
            puzzle_id TEXT PRIMARY KEY,
            fen TEXT NOT NULL,
            moves TEXT NOT NULL,
            rating INTEGER
        );

        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS openings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS puzzle_themes (
            puzzle_id TEXT,
            theme_id INTEGER,
            PRIMARY KEY (puzzle_id, theme_id),
            FOREIGN KEY (puzzle_id) REFERENCES puzzles(puzzle_id),
            FOREIGN KEY (theme_id) REFERENCES themes(id)
        );

        CREATE TABLE IF NOT EXISTS puzzle_openings (
            puzzle_id TEXT,
            opening_id INTEGER,
            PRIMARY KEY (puzzle_id, opening_id),
            FOREIGN KEY (puzzle_id) REFERENCES puzzles(puzzle_id),
            FOREIGN KEY (opening_id) REFERENCES openings(id)
        );
    """)


def get_or_create(cursor, table, name):
    """Inserta un valor único y devuelve su id (tema o apertura)."""
    cursor.execute(f"SELECT id FROM {table} WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    return cursor.lastrowid


def convert_csv_to_sqlite():
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"ERROR: No se encontró {CSV_FILE}")
        return

    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()

    print("Creando tablas...")
    create_tables(cursor)
    conn.commit()

    print("Importando puzzles...")
    total = 0
    skipped = 0

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:

            # Filtrar puzzles inestables
            try:
                if int(row["RatingDeviation"]) >= rating_deviation_threshold:
                    skipped += 1
                    continue
            except ValueError:
                skipped += 1
                continue

            puzzle_id = row["PuzzleId"]
            fen = row["FEN"]
            moves = row["Moves"]
            rating = int(row["Rating"])

            # Insertar puzzle
            cursor.execute("""
                INSERT OR REPLACE INTO puzzles (puzzle_id, fen, moves, rating)
                VALUES (?, ?, ?, ?)
            """, (puzzle_id, fen, moves, rating))

            # ----- Procesar temas -----
            themes = row["Themes"].split()
            for theme in themes:
                theme_id = get_or_create(cursor, "themes", theme)
                cursor.execute("""
                    INSERT OR IGNORE INTO puzzle_themes (puzzle_id, theme_id)
                    VALUES (?, ?)
                """, (puzzle_id, theme_id))

            # ----- Procesar aperturas -----
            openings = row["OpeningTags"].split()
            for opening in openings:
                opening_id = get_or_create(cursor, "openings", opening)
                cursor.execute("""
                    INSERT OR IGNORE INTO puzzle_openings (puzzle_id, opening_id)
                    VALUES (?, ?)
                """, (puzzle_id, opening_id))

            total += 1

            if total % 5000 == 0:
                conn.commit()
                print(f"{total} puzzles procesados...")

    conn.commit()
    conn.close()

    print("==========================================")
    print(f"Importación terminada")
    print(f"Puzzles insertados: {total}")
    print(f"Puzzles descartados: {skipped}")
    print(f"Base SQLite creada: {SQLITE_FILE}")
    print("==========================================")


if __name__ == "__main__":
    convert_csv_to_sqlite()