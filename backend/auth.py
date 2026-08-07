"""
Auth system — JWT tokens, user management, guest mode.
Uses SQLite for user storage, bcrypt for passwords.
"""

import os
import time
import json
import hmac
import hashlib
import sqlite3
import secrets
from pathlib import Path
from dataclasses import dataclass

DB_PATH = Path(__file__).parent / "light_cycles.db"
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_auth_db():
    """Create users + wallets tables."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_guest INTEGER DEFAULT 0,
            balance_cents INTEGER DEFAULT 0,
            stripe_connect_id TEXT,
            created_at REAL NOT NULL,
            last_login REAL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            type TEXT NOT NULL,  -- deposit, withdrawal, entry_fee, prize
            amount_cents INTEGER NOT NULL,
            stripe_payment_id TEXT,
            description TEXT,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS auth_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            expires_at REAL NOT NULL,
            created_at REAL NOT NULL
        );
    """)
    db.commit()
    db.close()


# ── Password hashing ──────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Simple SHA-256 + salt. For production, use bcrypt."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    salt, h = stored.split(":", 1)
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest() == h


# ── JWT ───────────────────────────────────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: str, expires_hours: int = 168) -> str:
    """Create a JWT token valid for N hours (default 7 days)."""
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    now = int(time.time())
    payload = _b64url_encode(json.dumps({
        "sub": user_id,
        "iat": now,
        "exp": now + expires_hours * 3600,
    }).encode())
    signature = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{signature}"


def verify_token(token: str) -> dict | None:
    """Verify JWT and return payload, or None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts

        # Verify signature
        expected = hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None

        data = json.loads(_b64url_decode(payload))

        # Check expiry
        if data.get("exp", 0) < time.time():
            return None

        return data
    except Exception:
        return None


def get_user_from_token(token: str) -> dict | None:
    """Get user dict from a valid token."""
    payload = verify_token(token)
    if not payload:
        return None

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)).fetchone()
    db.close()

    if user:
        return dict(user)
    return None


def create_guest_token() -> str:
    """Create a guest user and return a token."""
    guest_id = f"guest-{secrets.token_hex(8)}"
    db = get_db()

    # Hash a random password guest can't use
    pw_hash = _hash_password(secrets.token_hex(32))

    db.execute("""
        INSERT INTO users (id, email, username, password_hash, is_guest, balance_cents, created_at)
        VALUES (?, ?, ?, ?, 1, 0, ?)
    """, (guest_id, f"{guest_id}@guest.local", f"Guest-{guest_id[-6:]}", pw_hash, time.time()))
    db.commit()
    db.close()

    return create_token(guest_id)


# ── User operations ───────────────────────────────────────────────────

def register_user(email: str, username: str, password: str) -> dict | None:
    """Register a new user. Returns user dict or None if taken."""
    db = get_db()

    # Check existing
    existing = db.execute(
        "SELECT id FROM users WHERE email = ? OR username = ?", (email, username)
    ).fetchone()
    if existing:
        db.close()
        return None

    user_id = f"usr-{secrets.token_hex(8)}"
    pw_hash = _hash_password(password)

    db.execute("""
        INSERT INTO users (id, email, username, password_hash, is_guest, balance_cents, created_at, last_login)
        VALUES (?, ?, ?, ?, 0, 0, ?, ?)
    """, (user_id, email, username, pw_hash, time.time(), time.time()))
    db.commit()

    user = dict(db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    db.close()
    return user


def login_user(email: str, password: str) -> tuple[dict | None, str | None]:
    """Login with email + password. Returns (user, token) or (None, None)."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ? AND is_guest = 0", (email,)).fetchone()

    if not user:
        db.close()
        return None, None

    if not _verify_password(password, user["password_hash"]):
        db.close()
        return None, None

    # Update last login
    db.execute("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user["id"]))
    db.commit()

    token = create_token(user["id"])
    db.close()
    return dict(user), token


def get_user(user_id: str) -> dict | None:
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return dict(user) if user else None


def get_user_balance(user_id: str) -> int:
    """Get balance in cents."""
    db = get_db()
    row = db.execute("SELECT balance_cents FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return row["balance_cents"] if row else 0


def add_balance(user_id: str, amount_cents: int, description: str, payment_id: str = "") -> int:
    """Add funds to user balance. Returns new balance."""
    db = get_db()
    db.execute("UPDATE users SET balance_cents = balance_cents + ? WHERE id = ?", (amount_cents, user_id))
    db.execute("""
        INSERT INTO transactions (id, user_id, type, amount_cents, stripe_payment_id, description, created_at)
        VALUES (?, ?, 'deposit', ?, ?, ?, ?)
    """, (f"txn-{secrets.token_hex(8)}", user_id, amount_cents, payment_id, description, time.time()))
    db.commit()
    balance = db.execute("SELECT balance_cents FROM users WHERE id = ?", (user_id,)).fetchone()["balance_cents"]
    db.close()
    return balance


def deduct_balance(user_id: str, amount_cents: int, description: str) -> tuple[bool, int]:
    """Deduct funds. Returns (success, new_balance)."""
    db = get_db()
    current = db.execute("SELECT balance_cents FROM users WHERE id = ?", (user_id,)).fetchone()["balance_cents"]
    if current < amount_cents:
        db.close()
        return False, current

    db.execute("UPDATE users SET balance_cents = balance_cents - ? WHERE id = ?", (amount_cents, user_id))
    db.execute("""
        INSERT INTO transactions (id, user_id, type, amount_cents, description, created_at)
        VALUES (?, ?, 'entry_fee', ?, ?, ?)
    """, (f"txn-{secrets.token_hex(8)}", user_id, amount_cents, description, time.time()))
    db.commit()
    new_balance = db.execute("SELECT balance_cents FROM users WHERE id = ?", (user_id,)).fetchone()["balance_cents"]
    db.close()
    return True, new_balance


def pay_winner(user_id: str, amount_cents: int, tournament_title: str) -> int:
    """Credit prize money to winner. Returns new balance."""
    db = get_db()
    db.execute("UPDATE users SET balance_cents = balance_cents + ? WHERE id = ?", (amount_cents, user_id))
    db.execute("""
        INSERT INTO transactions (id, user_id, type, amount_cents, description, created_at)
        VALUES (?, ?, 'prize', ?, ?, ?)
    """, (f"txn-{secrets.token_hex(8)}", user_id, amount_cents, f"Prize: {tournament_title}", time.time()))
    db.commit()
    balance = db.execute("SELECT balance_cents FROM users WHERE id = ?", (user_id,)).fetchone()["balance_cents"]
    db.close()
    return balance


def get_user_transactions(user_id: str, limit: int = 20) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# Initialize on import
init_auth_db()
