import os
import secrets
import sqlite3
import string
from contextlib import contextmanager
from io import BytesIO
from PIL import Image, ImageOps

DB_FILE = "auction.db"
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)


@contextmanager
def db():
    """Open the database, save changes if all went well, undo them if not, always close."""
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                sport TEXT NOT NULL,
                event_date TEXT,
                registration_open INTEGER NOT NULL DEFAULT 1,
                min_age INTEGER NOT NULL DEFAULT 10,
                max_age INTEGER NOT NULL DEFAULT 70,
                registration_deadline TEXT,
                is_public INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL REFERENCES tournaments(id),
                number INTEGER NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                age INTEGER NOT NULL,
                village TEXT NOT NULL,
                phone TEXT NOT NULL,
                photo_path TEXT,
                flag_dismissed INTEGER NOT NULL DEFAULT 0,
                UNIQUE (tournament_id, number)
            )
        """)

# ---------------- tournaments ----------------
def create_tournament(name, sport, event_date, min_age, max_age, deadline, is_public):
    alphabet = string.ascii_lowercase + string.digits
    for _ in range(5):
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        try:
            with db() as conn:
                conn.execute(
                    """INSERT INTO tournaments
                       (code, name, sport, event_date, min_age, max_age,
                        registration_deadline, is_public)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (code, name, sport, event_date, min_age, max_age,
                     deadline, 1 if is_public else 0),
                )
            return code
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("Could not generate a unique tournament code")


def get_tournament_by_code(code):
    with db() as conn:
        row = conn.execute("SELECT * FROM tournaments WHERE code = ?", (code,)).fetchone()
        return dict(row) if row else None


def list_tournaments():
    with db() as conn:
        rows = conn.execute("SELECT * FROM tournaments ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def set_registration_open(tournament_id, is_open):
    with db() as conn:
        conn.execute(
            "UPDATE tournaments SET registration_open = ? WHERE id = ?",
            (1 if is_open else 0, tournament_id),
        )


# ---------------- players ----------------
def save_photo(uploaded_bytes, tournament_id, number):
    """Resize the photo so huge phone pictures don't bloat storage or the PDF."""
    img = Image.open(BytesIO(uploaded_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img.thumbnail((800, 800))
    path = os.path.join(PHOTO_DIR, f"{tournament_id}_{number}.jpg")
    img.save(path, "JPEG", quality=85)
    return path


def add_player(tournament_id, name, role, age, village, phone, photo_bytes):
    with db() as conn:
        # Lock the database for writing so two people registering at the
        # same moment can't both receive the same player number.
        conn.execute("BEGIN IMMEDIATE")
        number = conn.execute(
            "SELECT COALESCE(MAX(number), 0) + 1 FROM players WHERE tournament_id = ?",
            (tournament_id,),
        ).fetchone()[0]
        path = save_photo(photo_bytes, tournament_id, number)
        conn.execute(
            """INSERT INTO players
               (tournament_id, number, name, role, age, village, phone, photo_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tournament_id, number, name, role, age, village, phone, path),
        )
        return number


def get_player(tournament_id, number):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM players WHERE tournament_id = ? AND number = ?",
            (tournament_id, number),
        ).fetchone()
        return dict(row) if row else None


def get_all_players(tournament_id):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM players WHERE tournament_id = ? ORDER BY number",
            (tournament_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def count_players(tournament_id):
    with db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM players WHERE tournament_id = ?", (tournament_id,)
        ).fetchone()[0]