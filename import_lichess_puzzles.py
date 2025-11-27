import csv
import sqlite3
from pathlib import Path

# ----- CONFIG -----
CSV_FILE = "lichess_db_puzzle.csv"        
SQLITE_FILE = "lichess_puzzles.sqlite3"
rating_deviation_threshold = 76
BATCH_SIZE = 5000                       
# -------------------

def create_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS puzzles (
            puzzle_id TEXT PRIMARY KEY,
            fen TEXT NOT NULL,
            moves TEXT NOT NULL,
            rating INTEGER,
            themes TEXT,
            opening_tags TEXT
        );
    """)

def convert_csv_to_sqlite():
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"ERROR: No se encontró {CSV_FILE}")
        return

    conn = sqlite3.connect(SQLITE_FILE)
    cursor = conn.cursor()

    print("Creando tabla...")
    create_table(cursor)
    conn.commit()

    print("Importando puzzles...")
    batch = []
    total = 0
    skipped = 0

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:

            # Filtrar puzzles estables: rating_deviation < rating_deviation_threshold
            try:
                if int(row["RatingDeviation"]) >= rating_deviation_threshold:
                    skipped += 1
                    continue
            except ValueError:
                skipped += 1
                continue

            batch.append((
                row["PuzzleId"],
                row["FEN"],
                row["Moves"],
                int(row["Rating"]),
                row["Themes"],
                row["OpeningTags"],
            ))

            # insert batch
            if len(batch) >= BATCH_SIZE:
                cursor.executemany("""
                    INSERT OR REPLACE INTO puzzles (
                        puzzle_id, fen, moves, rating, themes, opening_tags
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                total += len(batch)
                print(f"{total} puzzles insertados...")
                batch.clear()

    # Insertar último batch
    if batch:
        cursor.executemany("""
            INSERT OR REPLACE INTO puzzles (
                puzzle_id, fen, moves, rating, themes, opening_tags
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()
        total += len(batch)

    conn.close()

    print("==========================================")
    print(f"Importación terminada")
    print(f"Puzzles insertados: {total}")
    print(f"Puzzles descartados: {skipped}")
    print(f"Base SQLite creada: {SQLITE_FILE}")
    print("==========================================")


if __name__ == "__main__":
    convert_csv_to_sqlite()
