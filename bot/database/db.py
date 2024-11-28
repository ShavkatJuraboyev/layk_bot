import aiosqlite
import os

# Define a directory for the database
DB_DIR = "data"  # Or any other directory you want to use
DB_PATH = os.path.join(DB_DIR, "bot.db")  # Combine directory with filename

# Ensure the directory exists
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

async def init_db():
    try:
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
                name TEXT,
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
    except Exception as e:
        print(f"Error initializing database: {e}")



async def add_channel(name, link):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO channels (name, link) VALUES (?, ?)", (name, link))
            await db.commit()
    except Exception as e:
        print(f"Error adding channel: {e}")

async def get_channels():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name, link FROM channels")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting channels: {e}")
        return []

async def add_video(file_id, name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO videos (file_id, name) VALUES (?, ?)", (file_id, name))
            await db.commit()
    except Exception as e:
        print(f"Error adding video: {e}")

async def get_videos():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT id, file_id, name, likes, dislikes FROM videos")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting videos: {e}")
        return []

async def like_video(user_id, video_id, like=True):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
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
        print(f"IntegrityError: User {user_id} has already voted for video {video_id}.")
        return False
    except Exception as e:
        print(f"Error liking video: {e}")
        return False

# database/db.py
async def get_video_votes(video_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT likes, dislikes FROM videos WHERE id = :video_id", {"video_id": video_id})
            result = await cursor.fetchone()
            print(result)  # Natijani tekshirish
            if result:
                return {"likes": result[0], "dislikes": result[1]}
            return {"likes": 0, "dislikes": 0}
    except Exception as e:
        print(f"Error getting votes for video_id={video_id}: {e}")