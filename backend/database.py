import sqlite3

# connect to database
conn = sqlite3.connect("data/health_data.db", check_same_thread=False)
cursor = conn.cursor()

# create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS medications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    time TEXT
)
""")

conn.commit()


# add medication
def add_medication(name, time):
    cursor.execute(
        "INSERT INTO medications (name, time) VALUES (?, ?)",
        (name, time)
    )
    conn.commit()


# get medications
def get_medications():
    cursor.execute("SELECT * FROM medications")
    return cursor.fetchall()