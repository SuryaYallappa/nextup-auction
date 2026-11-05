import os
import sqlite3
from io import BytesIO
from PIL import Image, ImageOps

DB_FILE = "auction.db"
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                age INTEGER NOT NULL,
                village TEXT NOT NULL,
                photo_path TEXT
            )
        """)


def save_photo(uploaded_bytes, player_id):
    """Resize the photo so huge phone pictures don't bloat storage or the PDF."""
    img = Image.open(BytesIO(uploaded_bytes))
    img = ImageOps.exif_transpose(img)   # fixes phone photos that appear rotated
    img = img.convert("RGB")
    img.thumbnail((800, 800))            # max 800px on the longest side
    path = os.path.join(PHOTO_DIR, f"{player_id}.jpg")
    img.save(path, "JPEG", quality=85)
    return path


def add_player(name, role, age, village, photo_bytes):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO players (name, role, age, village) VALUES (?, ?, ?, ?)",
            (name, role, age, village),
        )
        player_id = cur.lastrowid  # the auto-generated player number
        path = save_photo(photo_bytes, player_id)
        conn.execute("UPDATE players SET photo_path = ? WHERE id = ?", (path, player_id))
    return player_id


def get_player(player_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    return dict(row) if row else None


def count_players():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

def get_all_players():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM players ORDER BY id").fetchall()
    return [dict(r) for r in rows]    