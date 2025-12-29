import aiosqlite
import os

# Ma'lumotlar bazasi uchun katalogni belgilang
DB_DIR = "data"  #Yoki siz foydalanmoqchi bo'lgan boshqa katalog
DB_PATH = os.path.join(DB_DIR, "bot.db")  #Katalogni fayl nomi bilan birlashtiring

# Katalog mavjudligiga ishonch hosil qiling
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
            
            await db.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name TEXT, 
                photo_id TEXT
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE CASCADE
            )""")

            await db.execute("""
            CREATE TABLE IF NOT EXISTS emplyee_likes (
                user_id INTEGER,
                name_id INTEGER,
                UNIQUE(user_id, name_id)
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

async def delete_channel(name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM channels WHERE name = ?", (name,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting channel: {e}")

async def edit_channel(old_name, new_name, new_link):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE channels SET name = ?, link = ? WHERE name = ?",
                (new_name, new_link, old_name),
            )
            await db.commit()
    except Exception as e:
        print(f"Error editing channel: {e}")


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

async def delete_video(name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM videos WHERE name = ?", (name,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting channel: {e}")

async def edit_video(old_name, new_name, file_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE videos SET name = ?, file_id = ? WHERE name = ?",
                (new_name, file_id, old_name),
            )
            await db.commit()
    except Exception as e:
        print(f"Error editing channel: {e}")

async def like_video(user_id, video_id, like=True):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Checking if the user has already voted
            cursor = await db.execute("SELECT 1 FROM user_likes WHERE user_id = ?", (user_id,)) 
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


async def add_department(department_name, photo_id):
    try:  
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO departments (department_name, photo_id) VALUES (?, ?)",
                (department_name, photo_id)
            )
            await db.commit()
    except Exception as e:
        print(f"Error adding department: {e}")

async def get_departments():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT id, department_name, photo_id FROM departments")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting department: {e}")
        return []

async def delete_department(department_name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM departments WHERE department_name = ?", (department_name,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting channel: {e}")

async def edit_department(old_name, new_name, photo_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE departments SET department_name = ?, photo_id = ? WHERE department_name = ?",
                (new_name, photo_id, old_name),
            )
            await db.commit()
    except Exception as e:
        print(f"Error editing channel: {e}")


async def add_employee(employee_name, department_id):
    try:  
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO employees (employee_name, department_id) VALUES (?, ?)",
                (employee_name, department_id)
            )
            await db.commit()
    except Exception as e:
        print(f"Error adding employe: {e}")

async def get_employees():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT * FROM employees")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting employees: {e}")
        return []

async def delete_employee(employee_name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM employees WHERE employee_name = ?", (employee_name,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting channel: {e}")

async def edit_employee(old_name, new_name, department_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE employees SET employee_name = ?, department_id = ? WHERE name = ?",
                (new_name, department_id, old_name),
            )
            await db.commit()
    except Exception as e:
        print(f"Error editing channel: {e}")

async def like_employee(user_id, name_id, like=True):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Foydalanuvchi allaqachon boshqa xodimga ovoz berganmi?
            cursor = await db.execute("SELECT 1 FROM emplyee_likes WHERE user_id = ?", (user_id,))
            if await cursor.fetchone():
                return False  # Bu foydalanuvchi allaqachon ovoz bergan

            await db.execute("INSERT INTO emplyee_likes (user_id, name_id) VALUES (?, ?)", (user_id, name_id))
            if like:
                await db.execute("UPDATE employees SET likes = likes + 1 WHERE id = ?", (name_id,))
            else:
                await db.execute("UPDATE employees SET dislikes = dislikes + 1 WHERE id = ?", (name_id,))
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        print(f"IntegrityError: User {user_id} has already voted.")
        return False
    except Exception as e:
        print(f"Error liking employee: {e}")
        return False


async def add_dekanat_to_department(department_name, employee_name, photo_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Departamentni topishga harakat qiling
            cursor = await db.execute(
                "SELECT id FROM departments WHERE department_name = ?",
                (department_name,)
            )
            department = await cursor.fetchone()
            
            if department:
                # Departament mavjud bo‘lsa, uning ID sini oling
                department_id = department[0]
            else:
                # Departament mavjud bo‘lmasa, uni yarating
                cursor = await db.execute(
                    "INSERT INTO departments (department_name, photo_id) VALUES (?, ?)",
                    (department_name, photo_id)
                )
                department_id = cursor.lastrowid
                print(f"{department_id}-{department_name} bo'limi yaratildi.")

            # Dekanat qo‘shish
            await db.execute(
                "INSERT INTO employees (employee_name, department_id) VALUES (?, ?)",
                (employee_name, department_id)
            )
            await db.commit()
            print(f"{employee_name} {department_name} bo'limiga qo'shildi.")
    except Exception as e:
        print(f"Error adding dekanat to department: {e}")

async def get_employees_by_department(department_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # department_id bo‘yicha dekanatlarni olish
            cursor = await db.execute(
                "SELECT * FROM employees WHERE department_id = ?",
                (department_id,)
            )
            dekanats = await cursor.fetchall()
            
            if dekanats:
                return dekanats  # Barcha topilgan yozuvlarni qaytarish
            else:
                print(f"Department ID {department_id} uchun dekanat topilmadi.")
                return []
    except Exception as e:
        print(f"Error fetching dekanats for department ID {department_id}: {e}")
        return []

async def get_users():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT * FROM users")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting employees: {e}")
        return []
    

async def delete_all_employee_likes():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("DELETE FROM emplyee_likes")
            print("O‘chirilgan like soni:", cursor.rowcount)
            await db.commit()
    except Exception as e:
        print(f"Error deleting employee likes: {e}")
