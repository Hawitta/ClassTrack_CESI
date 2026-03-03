import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# # Connect to local SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# # Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
     user_role INTEGER NOT NULL,
    password_hash TEXT NOT NULL
)
""")
conn.commit()

# username = "admin"
# password = "J33pvw@n9ler"

# username = "Hawiana"
# password = "J3as1m1h2026"

username = "John_123"
password = "Abeba1111"

# Hash the password
password_hash = generate_password_hash(password)
user_role = 2
# Insert into database
cursor.execute("INSERT INTO users (username, user_role, password_hash) VALUES (?, ?, ?)", 
               (username, user_role, password_hash))
conn.commit()