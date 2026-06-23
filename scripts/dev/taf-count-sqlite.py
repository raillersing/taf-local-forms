#!/usr/bin/env python3
"""Count records in the old SQLite database for migration audit."""
import os
import sys
import sqlite3

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "/app/data/db.sqlite3"

if not os.path.exists(DB_PATH):
    print(f"ERROR: {DB_PATH} not found")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables = [
    "surveys_trainingmodule",
    "surveys_trainingsession",
    "surveys_student",
    "surveys_submission",
    "surveys_module3submission",
    "surveys_module4submission",
    "surveys_module5submission",
    "surveys_module6submission",
    "surveys_module7submission",
    "surveys_formpresence",
    "auth_user",
]

print(f"SQLite DB: {DB_PATH} ({os.path.getsize(DB_PATH)} bytes)")
print("=" * 50)
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}")
    except sqlite3.OperationalError as e:
        print(f"  {table}: ERROR - {e}")

conn.close()
