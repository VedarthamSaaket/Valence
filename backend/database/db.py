import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "valence.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            google_id TEXT,
            avatar_color TEXT DEFAULT '#FF6B6B',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            test_type TEXT NOT NULL,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_responses TEXT NOT NULL,
            trait_scores TEXT NOT NULL,
            percentiles TEXT NOT NULL,
            archetype_id TEXT,
            archetype_name TEXT,
            archetype_description TEXT,
            umap_x REAL,
            umap_y REAL,
            similarity_pct REAL,
            rarity_pct REAL,
            neighborhood_traits TEXT,
            consented_to_dataset INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS unified_profiles (
            user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            master_archetype_id TEXT,
            master_archetype_name TEXT,
            unified_vector TEXT,
            completed_tests TEXT DEFAULT '[]',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );
    """)

    # Migration: enriched insights are persisted so they survive page
    # reloads and can be filled in asynchronously after submit.
    cols = [r[1] for r in cursor.execute("PRAGMA table_info(test_results)").fetchall()]
    if "insights" not in cols:
        cursor.execute("ALTER TABLE test_results ADD COLUMN insights TEXT")
    if "enrichment_status" not in cols:
        cursor.execute(
            "ALTER TABLE test_results ADD COLUMN enrichment_status TEXT DEFAULT 'none'"
        )

    cursor.execute(
        "UPDATE test_results SET enrichment_status = 'none' WHERE enrichment_status = 'pending'"
    )

    conn.commit()
    conn.close()
    print("Database initialized.")
