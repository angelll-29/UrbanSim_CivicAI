import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any

# Root & Database path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "urbansim_users.db")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite users database with tables and seed accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'CITIZEN',
            ward TEXT NOT NULL DEFAULT 'GS',
            phone TEXT,
            address TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Seed Default Accounts if database is newly initialized
    seed_users = [
        ("citizen", "citizen@urbansim.local", "Aarav Sharma", hash_password("citizen123"), "CITIZEN", "GS", "+91 98200 12345", "Worli, Mumbai"),
        ("analyst", "analyst@urbansim.local", "Dr. Ananya Desai", hash_password("analyst123"), "URBAN_ANALYST", "All", "+91 98200 67890", "BKC, Mumbai"),
        ("authority", "authority@urbansim.local", "Rajesh Kulkarni (BMC Asst. Commissioner)", hash_password("authority123"), "URBAN_AUTHORITY", "All", "+91 98200 11223", "BMC HQ, Fort"),
        ("admin", "admin@urbansim.local", "System Administrator", hash_password("admin123"), "SYSTEM_ADMIN", "All", "+91 98200 99887", "IT Cell, BMC")
    ]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for username, email, name, pwd_hash, role, ward, phone, addr in seed_users:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("""
                INSERT INTO users (username, email, name, password_hash, role, ward, phone, address, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (username, email, name, pwd_hash, role, ward, phone, addr, now, now))

    conn.commit()
    conn.close()

# Initialize DB on module import
init_db()

# --------------------------------------------------
# DATABASE QUERY & PERSISTENCE HELPERS
# --------------------------------------------------

def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    clean = identifier.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email, name, password_hash, role, ward, phone, address, is_active, created_at, updated_at
        FROM users
        WHERE LOWER(username) = ? OR LOWER(email) = ?
    """, (clean, clean))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_citizen_in_db(
    username: str,
    email: str,
    name: str,
    password: str,
    ward: str = "GS",
    phone: Optional[str] = None,
    address: Optional[str] = None
) -> Dict[str, Any]:
    """Persist a newly registered citizen into SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for existing username or email
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username.strip().lower(),))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Username '{username}' is already registered.")

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Email '{email}' is already registered with another account.")

    pwd_hash = hash_password(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO users (username, email, name, password_hash, role, ward, phone, address, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'CITIZEN', ?, ?, ?, 1, ?, ?)
    """, (
        username.strip().lower(),
        email.strip().lower(),
        name.strip(),
        pwd_hash,
        ward.strip().upper(),
        phone.strip() if phone else None,
        address.strip() if address else None,
        now,
        now
    ))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "username": username.strip().lower(),
        "email": email.strip().lower(),
        "name": name.strip(),
        "role": "CITIZEN",
        "ward": ward.strip().upper(),
        "phone": phone,
        "address": address,
        "is_active": True,
        "created_at": now
    }

def list_all_users() -> List[Dict[str, Any]]:
    """Retrieve all users stored in the SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email, name, role, ward, phone, address, is_active, created_at
        FROM users
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_counts_by_role() -> Dict[str, int]:
    """Get aggregate count of registered users per role."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
    rows = cursor.fetchall()
    conn.close()
    counts = {r["role"]: r["count"] for r in rows}
    return counts
