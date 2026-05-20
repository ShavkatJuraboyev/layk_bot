import os
import aiosqlite
from contextlib import asynccontextmanager
from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@asynccontextmanager
async def connect():
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
    finally:
        await db.close()


async def init_db():
    async with connect() as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            username TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS start_page (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            photo_id TEXT,
            caption TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS mandatory_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            title TEXT NOT NULL,
            invite_link TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            photo_id TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            photo_id TEXT,
            video_id TEXT,
            caption TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, department_id),
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            place INTEGER NOT NULL,
            candidate_id INTEGER,
            custom_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(department_id, place),
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL
        )
        """)

        # Eski bot.db fayli bo‘lsa, yangi ustunlarni avtomatik qo‘shamiz.
        await migrate_db(db)
        await db.commit()


async def _table_columns(db, table_name: str) -> set[str]:
    cur = await db.execute(f"PRAGMA table_info({table_name})")
    rows = await cur.fetchall()
    return {row[1] for row in rows}


async def _add_column_if_missing(db, table_name: str, column_name: str, column_sql: str):
    columns = await _table_columns(db, table_name)
    if column_name not in columns:
        await db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


async def migrate_db(db):
    """Eski bazani o‘chirmasdan yangi kodga moslab beradi."""
    await _add_column_if_missing(db, "users", "full_name", "full_name TEXT")
    await _add_column_if_missing(db, "users", "username", "username TEXT")
    await _add_column_if_missing(db, "users", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")

    await _add_column_if_missing(db, "departments", "is_active", "is_active INTEGER DEFAULT 1")
    await _add_column_if_missing(db, "departments", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")

    await _add_column_if_missing(db, "candidates", "is_active", "is_active INTEGER DEFAULT 1")
    await _add_column_if_missing(db, "candidates", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")

    await _add_column_if_missing(db, "mandatory_channels", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")
    await _add_column_if_missing(db, "votes", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")
    await _add_column_if_missing(db, "results", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")


async def add_user(telegram_id: int, full_name: str = "", username: str = ""):
    async with connect() as db:
        await db.execute("""
        INSERT INTO users (telegram_id, full_name, username)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            full_name=excluded.full_name,
            username=excluded.username
        """, (telegram_id, full_name, username))
        await db.commit()


async def create_start_page(photo_id: str | None, caption: str | None):
    async with connect() as db:
        await db.execute("""
        INSERT OR REPLACE INTO start_page (id, photo_id, caption)
        VALUES (1, ?, ?)
        """, (photo_id, caption))
        await db.commit()


async def get_start_page():
    async with connect() as db:
        cur = await db.execute("SELECT photo_id, caption FROM start_page WHERE id=1")
        return await cur.fetchone()


async def delete_start_page():
    async with connect() as db:
        await db.execute("DELETE FROM start_page WHERE id=1")
        await db.commit()


async def add_channel(chat_id, title: str, invite_link: str):
    async with connect() as db:
        await db.execute("""
        INSERT INTO mandatory_channels (chat_id, title, invite_link)
        VALUES (?, ?, ?)
        """, (str(chat_id) if chat_id is not None else None, title, invite_link))
        await db.commit()


async def get_channels():
    async with connect() as db:
        cur = await db.execute("SELECT id, chat_id, title, invite_link FROM mandatory_channels ORDER BY id DESC")
        return await cur.fetchall()


async def get_channel(channel_id: int):
    async with connect() as db:
        cur = await db.execute("SELECT id, chat_id, title, invite_link FROM mandatory_channels WHERE id=?", (channel_id,))
        return await cur.fetchone()


async def delete_channel(channel_id: int):
    async with connect() as db:
        await db.execute("DELETE FROM mandatory_channels WHERE id=?", (channel_id,))
        await db.commit()


async def add_department(name: str, photo_id: str | None = None):
    async with connect() as db:
        cur = await db.execute("INSERT INTO departments (name, photo_id) VALUES (?, ?)", (name, photo_id))
        await db.commit()
        return cur.lastrowid


async def get_departments(include_closed: bool = True):
    async with connect() as db:
        if include_closed:
            cur = await db.execute("SELECT id, name, photo_id, is_active FROM departments ORDER BY id DESC")
        else:
            cur = await db.execute("SELECT id, name, photo_id, is_active FROM departments WHERE is_active=1 ORDER BY id DESC")
        return await cur.fetchall()


async def get_department(dep_id: int):
    async with connect() as db:
        cur = await db.execute("SELECT id, name, photo_id, is_active FROM departments WHERE id=?", (dep_id,))
        return await cur.fetchone()


async def update_department(dep_id: int, name: str | None = None, photo_id: str | None = None):
    async with connect() as db:
        await db.execute("""
        UPDATE departments
        SET name=COALESCE(?, name), photo_id=COALESCE(?, photo_id)
        WHERE id=?
        """, (name, photo_id, dep_id))
        await db.commit()


async def set_department_status(dep_id: int, is_active: bool):
    async with connect() as db:
        await db.execute("UPDATE departments SET is_active=? WHERE id=?", (1 if is_active else 0, dep_id))
        await db.commit()


async def delete_department(dep_id: int):
    async with connect() as db:
        await db.execute("DELETE FROM departments WHERE id=?", (dep_id,))
        await db.commit()


async def add_candidate(department_id: int, name: str, photo_id=None, video_id=None, caption=None):
    async with connect() as db:
        cur = await db.execute("""
        INSERT INTO candidates (department_id, name, photo_id, video_id, caption)
        VALUES (?, ?, ?, ?, ?)
        """, (department_id, name, photo_id, video_id, caption))
        await db.commit()
        return cur.lastrowid


async def get_candidates(department_id: int, active_only: bool = False):
    async with connect() as db:
        if active_only:
            cur = await db.execute("""
            SELECT id, department_id, name, photo_id, video_id, caption, is_active
            FROM candidates WHERE department_id=? AND is_active=1 ORDER BY id DESC
            """, (department_id,))
        else:
            cur = await db.execute("""
            SELECT id, department_id, name, photo_id, video_id, caption, is_active
            FROM candidates WHERE department_id=? ORDER BY id DESC
            """, (department_id,))
        return await cur.fetchall()


async def get_candidate_by_id(candidate_id: int):
    async with connect() as db:
        cur = await db.execute("""
        SELECT id, department_id, name, photo_id, video_id, caption, is_active
        FROM candidates WHERE id=?
        """, (candidate_id,))
        return await cur.fetchone()


async def update_candidate(candidate_id: int, name=None, photo_id=None, video_id=None, caption=None):
    async with connect() as db:
        await db.execute("""
        UPDATE candidates
        SET name=COALESCE(?, name),
            photo_id=COALESCE(?, photo_id),
            video_id=COALESCE(?, video_id),
            caption=COALESCE(?, caption)
        WHERE id=?
        """, (name, photo_id, video_id, caption, candidate_id))
        await db.commit()


async def clear_candidate_media(candidate_id: int):
    async with connect() as db:
        await db.execute("UPDATE candidates SET photo_id=NULL, video_id=NULL WHERE id=?", (candidate_id,))
        await db.commit()


async def set_candidate_status(candidate_id: int, is_active: bool):
    async with connect() as db:
        await db.execute("UPDATE candidates SET is_active=? WHERE id=?", (1 if is_active else 0, candidate_id))
        await db.commit()


async def delete_candidate(candidate_id: int):
    async with connect() as db:
        await db.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
        await db.commit()


async def vote(user_id: int, department_id: int, candidate_id: int) -> bool:
    async with connect() as db:
        dep_cur = await db.execute("SELECT is_active FROM departments WHERE id=?", (department_id,))
        dep = await dep_cur.fetchone()
        if not dep or dep[0] != 1:
            return False
        cand_cur = await db.execute("SELECT is_active FROM candidates WHERE id=? AND department_id=?", (candidate_id, department_id))
        cand = await cand_cur.fetchone()
        if not cand or cand[0] != 1:
            return False
        try:
            await db.execute("""
            INSERT INTO votes (user_id, department_id, candidate_id)
            VALUES (?, ?, ?)
            """, (user_id, department_id, candidate_id))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def user_vote(department_id: int, user_id: int):
    async with connect() as db:
        cur = await db.execute("""
        SELECT candidate_id FROM votes WHERE department_id=? AND user_id=?
        """, (department_id, user_id))
        return await cur.fetchone()


async def reset_votes_by_department(department_id: int):
    async with connect() as db:
        await db.execute("DELETE FROM votes WHERE department_id=?", (department_id,))
        await db.commit()


async def department_statistics(department_id: int):
    async with connect() as db:
        cur = await db.execute("""
        SELECT c.id, c.name, COUNT(v.id) AS votes
        FROM candidates c
        LEFT JOIN votes v ON v.candidate_id=c.id
        WHERE c.department_id=?
        GROUP BY c.id
        ORDER BY votes DESC, c.name ASC
        """, (department_id,))
        return await cur.fetchall()


async def count_all_votes(department_id: int) -> int:
    async with connect() as db:
        cur = await db.execute("SELECT COUNT(*) FROM votes WHERE department_id=?", (department_id,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def add_result(department_id: int, place: int, candidate_id=None, custom_name=None):
    async with connect() as db:
        await db.execute("""
        INSERT INTO results (department_id, place, candidate_id, custom_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(department_id, place) DO UPDATE SET
            candidate_id=excluded.candidate_id,
            custom_name=excluded.custom_name
        """, (department_id, place, candidate_id, custom_name))
        await db.commit()


async def get_results(department_id: int):
    async with connect() as db:
        cur = await db.execute("""
        SELECT r.id, r.department_id, r.place, r.candidate_id, r.custom_name, c.name
        FROM results r
        LEFT JOIN candidates c ON c.id=r.candidate_id
        WHERE r.department_id=?
        ORDER BY r.place ASC
        """, (department_id,))
        return await cur.fetchall()


async def delete_result(result_id: int):
    async with connect() as db:
        await db.execute("DELETE FROM results WHERE id=?", (result_id,))
        await db.commit()


async def delete_results(department_id: int):
    async with connect() as db:
        await db.execute("DELETE FROM results WHERE department_id=?", (department_id,))
        await db.commit()
