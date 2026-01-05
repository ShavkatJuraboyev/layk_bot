import aiosqlite
import os

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "bot.db")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)


# ======================================================
# INIT DATABASE
# ======================================================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        # USERS
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE
        )
        """)

        # START PAGE
        await db.execute("""
        CREATE TABLE IF NOT EXISTS start_page (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            photo_id TEXT,
            caption TEXT
        )
        """)

        # MANDATORY CHANNELS
        await db.execute("""
        CREATE TABLE IF NOT EXISTS mandatory_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            title TEXT,
            invite_link TEXT
        )
        """)

        # DEPARTMENTS
        await db.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            photo_id TEXT,
            is_active INTEGER DEFAULT 1
        )
        """)

        # CANDIDATES
        await db.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER,
            name TEXT,
            photo_id TEXT,
            video_id TEXT,
            caption TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
        )
        """)

        # VOTES
        await db.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER,
            department_id INTEGER,
            candidate_id INTEGER,
            UNIQUE(user_id, department_id)
        )
        """)

        # RESULTS
        await db.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER,
            place INTEGER,
            candidate_id INTEGER,
            custom_name TEXT
        )
        """)

        await db.commit()


# ======================================================
# USERS
# ======================================================
async def add_user(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
            (telegram_id,)
        )
        await db.commit()


# ======================================================
# START PAGE CRUD
# ======================================================
async def create_start_page(photo_id, caption):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO start_page (id, photo_id, caption)
        VALUES (1, ?, ?)
        """, (photo_id, caption))
        await db.commit()

async def get_start_page():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT photo_id, caption FROM start_page WHERE id=1
        """)
        return await cur.fetchone()


async def update_start_page(photo_id, caption):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE start_page
        SET photo_id=?, caption=?
        WHERE id=1
        """, (photo_id, caption))
        await db.commit()


async def delete_start_page():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        DELETE FROM start_page WHERE id=1
        """)
        await db.commit()



# ======================================================
# MANDATORY CHANNELS CRUD
# ======================================================
async def add_channel(chat_id, title, invite_link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO mandatory_channels (chat_id, title, invite_link)
        VALUES (?, ?, ?)
        """, (chat_id, title, invite_link))
        await db.commit()


async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM mandatory_channels")
        return await cur.fetchall()


async def update_channel(channel_id, title, invite_link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE mandatory_channels
        SET title=?, invite_link=?
        WHERE id=?
        """, (title, invite_link, channel_id))
        await db.commit()


async def delete_channel(channel_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM mandatory_channels WHERE id=?", (channel_id,))
        await db.commit()


# ======================================================
# DEPARTMENTS CRUD
# ======================================================
async def add_department(name, photo_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO departments (name, photo_id)
        VALUES (?, ?)
        """, (name, photo_id))
        await db.commit()


async def get_departments(include_closed=True):
    async with aiosqlite.connect(DB_PATH) as db:
        if include_closed:
            cur = await db.execute("SELECT * FROM departments")
        else:
            cur = await db.execute("SELECT * FROM departments WHERE is_active=1")
        return await cur.fetchall()

async def update_department(dep_id, name, photo_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE departments
        SET name=?, photo_id=?
        WHERE id=?
        """, (name, photo_id, dep_id))
        await db.commit()


async def set_department_status(dep_id, is_active: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE departments SET is_active=?
        WHERE id=?
        """, (1 if is_active else 0, dep_id))
        await db.commit()


async def delete_department(dep_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM departments WHERE id=?", (dep_id,))
        await db.commit()


# ======================================================
# CANDIDATES CRUD
# ======================================================
async def add_candidate(department_id, name, photo_id=None, video_id=None, caption=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO candidates
        (department_id, name, photo_id, video_id, caption)
        VALUES (?, ?, ?, ?, ?)
        """, (department_id, name, photo_id, video_id, caption))
        await db.commit()


async def get_candidates(department_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT * FROM candidates WHERE department_id=?
        """, (department_id,))
        return await cur.fetchall()


async def update_candidate(candidate_id, name=None, photo_id=None, video_id=None, caption=None, 
                           update_only_name=False, update_only_media=False, update_only_caption=False):
    async with aiosqlite.connect(DB_PATH) as db:
        if update_only_name:
            await db.execute("UPDATE candidates SET name=? WHERE id=?", (name, candidate_id))
        elif update_only_media:
            await db.execute("UPDATE candidates SET photo_id=?, video_id=? WHERE id=?", (photo_id, video_id, candidate_id))
        elif update_only_caption:
            await db.execute("UPDATE candidates SET caption=? WHERE id=?", (caption, candidate_id))
        else:
            await db.execute("""
                UPDATE candidates
                SET name = COALESCE(?, name),
                    photo_id = COALESCE(?, photo_id),
                    video_id = COALESCE(?, video_id),
                    caption = COALESCE(?, caption)
                WHERE id = ?
            """, (name, photo_id, video_id, caption, candidate_id))
        await db.commit()


async def get_candidate_by_id(candidate_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,))
        return await cur.fetchone()
    

async def delete_candidate(candidate_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM candidates WHERE id=?", (candidate_id,))
        await db.commit()


# ======================================================
# VOTING
# ======================================================
async def vote(user_id, department_id, candidate_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT 1 FROM votes
        WHERE user_id=? AND department_id=?
        """, (user_id, department_id))

        if await cur.fetchone():
            return False

        await db.execute("""
        INSERT INTO votes (user_id, department_id, candidate_id)
        VALUES (?, ?, ?)
        """, (user_id, department_id, candidate_id))
        await db.commit()
        return True


async def reset_votes_by_department(department_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM votes WHERE department_id=?", (department_id,))
        await db.commit()


# ======================================================
# RESULTS CRUD
# ======================================================
async def add_result(department_id, place, candidate_id=None, custom_name=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO results (department_id, place, candidate_id, custom_name)
        VALUES (?, ?, ?, ?)
        """, (department_id, place, candidate_id, custom_name))
        await db.commit()


async def get_results(department_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT * FROM results
        WHERE department_id=?
        ORDER BY place
        """, (department_id,))
        return await cur.fetchall()


async def delete_results(department_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM results WHERE department_id=?", (department_id,))
        await db.commit()


# ======================================================
# STATISTICS
# ======================================================
async def department_statistics(department_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT c.name, COUNT(v.candidate_id) as votes
        FROM candidates c
        LEFT JOIN votes v ON v.candidate_id = c.id
        WHERE c.department_id=?
        GROUP BY c.id
        ORDER BY votes DESC
        """, (department_id,))
        return await cur.fetchall()

async def get_results(department_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
        SELECT * FROM results
        WHERE department_id=?
        ORDER BY place
        """, (department_id,))
        return await cur.fetchall()
