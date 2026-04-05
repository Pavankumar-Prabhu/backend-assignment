from __future__ import annotations

from pathlib import Path
import sqlite3

from .auth import hash_password
from .utils import utc_now


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('viewer', 'analyst', 'admin')),
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS financial_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    entry_type TEXT NOT NULL CHECK (entry_type IN ('income', 'expense')),
    category TEXT NOT NULL,
    entry_date TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_by_user_id INTEGER NOT NULL,
    updated_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    FOREIGN KEY(created_by_user_id) REFERENCES users(id),
    FOREIGN KEY(updated_by_user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_tokens_token ON auth_tokens(token);
CREATE INDEX IF NOT EXISTS idx_records_date ON financial_records(entry_date);
CREATE INDEX IF NOT EXISTS idx_records_category ON financial_records(category);
CREATE INDEX IF NOT EXISTS idx_records_type ON financial_records(entry_type);
"""


DEFAULT_USERS = (
    ("Admin User", "admin@finance.local", "Admin123!", "admin", "active"),
    ("Analyst User", "analyst@finance.local", "Analyst123!", "analyst", "active"),
    ("Viewer User", "viewer@finance.local", "Viewer123!", "viewer", "active"),
)


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)
            self._seed_default_users(connection)
            connection.commit()

    def _seed_default_users(self, connection: sqlite3.Connection) -> None:
        existing_user_count = connection.execute(
            "SELECT COUNT(*) AS count FROM users WHERE deleted_at IS NULL"
        ).fetchone()["count"]
        if existing_user_count > 0:
            return

        now = utc_now()
        for full_name, email, password, role, status in DEFAULT_USERS:
            connection.execute(
                """
                INSERT INTO users (full_name, email, password_hash, role, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (full_name, email, hash_password(password), role, status, now, now),
            )

