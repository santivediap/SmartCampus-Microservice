# DB connection
import sqlite3

DB_PATH = "database.db"

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row