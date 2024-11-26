import aiosqlite

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            is_member BOOLEAN DEFAULT 0
        )""")
        
        # Kanallar va guruhlar jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            link TEXT
        )""")
        
        # Videolar jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0
        )""")
        
        # Foydalanuvchi ovozlari jadvali
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_likes (
            user_id INTEGER,
            video_id INTEGER,
            UNIQUE(user_id, video_id)
        )""")
        
        await db.commit()

async def add_channel(name, link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO channels (name, link) VALUES (?, ?)", (name, link))
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT name, link FROM channels")
        return await cursor.fetchall()

async def add_video(file_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO videos (file_id) VALUES (?)", (file_id,))
        await db.commit()

async def get_videos():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, file_id, likes, dislikes FROM videos")
        return await cursor.fetchall()

async def like_video(user_id, video_id, like=True):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            # Checking if the user has already voted
            cursor = await db.execute("SELECT 1 FROM user_likes WHERE user_id = ? AND video_id = ?", (user_id, video_id))
            if await cursor.fetchone():
                return False  # User has already voted

            await db.execute("INSERT INTO user_likes (user_id, video_id) VALUES (?, ?)", (user_id, video_id))
            if like:
                await db.execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (video_id,))
            else:
                await db.execute("UPDATE videos SET dislikes = dislikes + 1 WHERE id = ?", (video_id,))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False
