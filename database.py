import sqlite3
import datetime
from typing import Optional, List, Dict, Any

DB_PATH = "kino_bot.db"

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Foydalanuvchilar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Kinolar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    code TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    file_type TEXT DEFAULT 'video',
                    caption TEXT,
                    views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Adminlar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    role TEXT DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sozlamalar jadvali (masalan admin paroli)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Boshlang'ich admin parolini o'rnatish
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_password', 'davlat20102412')")

            # Majburiy kanallar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_link TEXT NOT NULL
                )
            """)
            conn.commit()

    # --- FOYDALANUVCHILAR ---
    def add_user(self, user_id: int, full_name: str, username: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO users (user_id, full_name, username, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, username, datetime.datetime.now()))
            conn.commit()

    def get_users_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]

    def get_all_users(self) -> List[int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            return [row["user_id"] for row in cursor.fetchall()]

    # --- KINOLAR ---
    def add_movie(self, code: str, file_id: str, file_type: str = "video", caption: str = "") -> bool:
        clean_code = str(code).strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO movies (code, file_id, file_type, caption, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (clean_code, file_id, file_type, caption, datetime.datetime.now()))
                conn.commit()
                return True
            except Exception as e:
                print(f"Xatolik kino qo'shishda: {e}")
                return False

    def get_movie(self, code: str) -> Optional[Dict[str, Any]]:
        clean_code = str(code).strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE code = ?", (clean_code,))
            row = cursor.fetchone()
            if row:
                # Ko'rishlar sonini 1 taga oshiramiz
                cursor.execute("UPDATE movies SET views = views + 1 WHERE code = ?", (clean_code,))
                conn.commit()
                return dict(row)
            return None

    def delete_movie(self, code: str) -> bool:
        clean_code = str(code).strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movies WHERE code = ?", (clean_code,))
            conn.commit()
            return cursor.rowcount > 0

    def get_movies_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM movies")
            return cursor.fetchone()[0]

    def get_recent_movies(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- ADMINLAR ---
    def is_admin(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def add_admin(self, user_id: int, role: str = "admin") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO admins (user_id, role, created_at)
                VALUES (?, ?, ?)
            """, (user_id, role, datetime.datetime.now()))
            conn.commit()
            return True

    def remove_admin(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_admins(self) -> List[int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            return [row["user_id"] for row in cursor.fetchall()]

    # --- SOZLAMALAR ---
    def get_admin_password(self) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'admin_password'")
            row = cursor.fetchone()
            if row:
                return row["value"]
            return "7777"

    def set_admin_password(self, new_password: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_password', ?)", (new_password.strip(),))
            conn.commit()
            return True

    # --- MAJBURIY KANALLAR ---
    def add_channel(self, channel_id: str, channel_name: str, channel_link: str) -> bool:
        clean_id = str(channel_id).strip()
        clean_name = str(channel_name).strip()
        clean_link = str(channel_link).strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO channels (channel_id, channel_name, channel_link)
                VALUES (?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    channel_name = excluded.channel_name,
                    channel_link = excluded.channel_link
            """, (clean_id, clean_name, clean_link))
            conn.commit()
            return True

    def remove_channel_by_id(self, channel_db_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM channels WHERE id = ?", (channel_db_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_channels(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

db = Database()
