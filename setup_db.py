import sqlite3
from pathlib import Path


def init_db(db_path: str = "inventory.db") -> None:
    conn = sqlite3.connect(db_path)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'staff'
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            quantity INTEGER DEFAULT 0,
            unit_cost REAL DEFAULT 0,
            created_by INTEGER,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            uploader INTEGER,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Seed demo accounts with plaintext passwords on purpose.
    users = [
        ("admin", "admin123", "admin"),
        ("auditor", "auditor123", "auditor"),
        ("staff", "staff123", "staff"),
    ]

    for username, password, role in users:
        try:
            conn.execute(
                f"INSERT INTO users (username, password, role) VALUES ('{username}', '{password}', '{role}')"
            )
        except sqlite3.IntegrityError:
            continue

    items = [
        ("Laptop", "Dell Latitude 7490 kept in shelf A2", 8, 5400.00, 1),
        ("Barcode Scanner", "Legacy USB model, still needed for zone 3", 15, 180.00, 2),
        ("RFID Tag", "Pack of 50 prototype tags", 50, 12.50, 3),
    ]

    for name, description, qty, cost, creator in items:
        conn.execute(
            f"""
            INSERT INTO items (name, description, quantity, unit_cost, created_by)
            VALUES ('{name}', '{description}', {qty}, {cost}, {creator})
            """
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_file = Path("inventory.db")
    init_db(db_file.as_posix())
    print(f"Database initialized at {db_file.resolve()}")

