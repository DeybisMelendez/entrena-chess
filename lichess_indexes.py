#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import sys


DB_PATH = Path("lichess_puzzles.sqlite3")


def ensure_indexes(db_path: Path):
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        -- Índice para filtros por rating
        CREATE INDEX IF NOT EXISTS idx_puzzles_rating
        ON puzzles(rating);

        -- Índice para búsqueda de themes por nombre
        CREATE INDEX IF NOT EXISTS idx_themes_name
        ON themes(name);

        -- Índices para joins en puzzle_themes
        CREATE INDEX IF NOT EXISTS idx_puzzle_themes_puzzle
        ON puzzle_themes(puzzle_id);

        CREATE INDEX IF NOT EXISTS idx_puzzle_themes_theme
        ON puzzle_themes(theme_id);
    """)

    conn.commit()
    conn.close()


def main():
    print("🔧 Ensuring SQLite indexes for Lichess puzzles DB...")
    ensure_indexes(DB_PATH)
    print("✅ Indexes ensured successfully.")


if __name__ == "__main__":
    main()
