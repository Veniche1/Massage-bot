import aiosqlite
from datetime import datetime

DB_NAME = "/data/users.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                full_name TEXT,
                age INTEGER
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                time TEXT,
                service TEXT,
                status TEXT DEFAULT 'pending',
                cancel_reason TEXT,    
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE
            )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        appointment_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (appointment_id) REFERENCES appointments (id)
            )
        """)
        
        await db.commit()

async def get_user_by_db_id(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None  
        return row

    
async def add_user(user_id, full_name, age):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, full_name, age) VALUES (?, ?, ?)",
            (user_id, full_name, age)
        )
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()


async def add_appointment(user_id, date, time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO appointments (user_id, date, time, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, date, time, "pending", datetime.now().isoformat())
        )
        await db.commit()


async def get_user_appointment_on_date(user_id: int, date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM appointments WHERE user_id = ? AND date = ? AND status != 'canceled'",
            (user_id, date)
        )
        return await cursor.fetchone()


async def is_time_taken(date: str, time: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM appointments WHERE date = ? AND time = ? AND status != 'canceled'",
            (date, time)
        )
        return await cursor.fetchone() is not None


async def get_booked_dates():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT DISTINCT date FROM appointments WHERE status != 'canceled'"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_all_appointments(status: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if status:
            cursor = await db.execute(
                "SELECT * FROM appointments WHERE status = ? ORDER BY date, time",
                (status,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM appointments ORDER BY date, time"
            )
        rows = await cursor.fetchall()
        return rows

async def update_appointment_status(appointment_id: int, status: str, reason: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if reason:
            await db.execute(
                "UPDATE appointments SET status = ?, cancel_reason = ? WHERE id = ?",
                (status, reason, appointment_id)
            )
        else:
            await db.execute(
                "UPDATE appointments SET status = ? WHERE id = ?",
                (status, appointment_id)
            )
        await db.commit()


async def get_appointment_by_id(appointment_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM appointments WHERE id = ?",  
            (appointment_id,)
        )
        return await cursor.fetchone()




async def block_date(date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)",
            (date,)
        )
        await db.commit()


async def unblock_date(date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM blocked_dates WHERE date = ?",
            (date,)
        )
        await db.commit()


async def get_blocked_dates():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT date FROM blocked_dates ORDER BY date")
        return await cursor.fetchall()

async def get_user_appointments(user_id: int):
    """Получает все записи пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, date, time, status, service FROM appointments WHERE user_id = ? ORDER BY date",
            (user_id,)
        )
        return await cursor.fetchall()


async def cancel_appointment(appointment_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE appointments SET status = 'canceled' WHERE id = ?",
            (appointment_id,)
        )
        await db.commit()


async def save_review(user_id: int, appointment_id: int, rating: int, comment: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, appointment_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, appointment_id, rating, comment, datetime.now().isoformat())
        )
        await db.commit()

async def get_reviews(limit: int = 5):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT u.full_name, r.rating, r.comment FROM reviews r JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC LIMIT ?",
            (limit,)
        )
        return await cursor.fetchall(  )