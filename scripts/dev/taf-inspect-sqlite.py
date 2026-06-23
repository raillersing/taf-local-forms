#!/usr/bin/env python3
"""Inspect SQLite data: users, students, FK relationships."""
import sqlite3

conn = sqlite3.connect("/app/data/db.sqlite3")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== auth_user ===")
cursor.execute("SELECT id, username, email, is_superuser, is_staff, is_active FROM auth_user ORDER BY id")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== surveys_student ===")
cursor.execute("SELECT id, user_id, first_name, last_name, email, class_name FROM surveys_student ORDER BY id")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== surveys_trainingsession ===")
cursor.execute("SELECT id, module_code, session_code, is_active FROM surveys_trainingsession ORDER BY id")
for row in cursor.fetchall():
    print(dict(row))

print("\n=== surveys_submission (M2) ===")
cursor.execute("SELECT id, student_id, session_id, full_name, email, score FROM surveys_submission ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows:
    print(dict(row))

print("\n=== surveys_module3submission ===")
cursor.execute("SELECT id, student_id, session_id, full_name, email, score FROM surveys_module3submission ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows:
    print(dict(row))

print("\n=== surveys_module4submission ===")
cursor.execute("SELECT id, student_id, session_id, full_name, email, score FROM surveys_module4submission ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows:
    print(dict(row))

print("\n=== surveys_module5submission ===")
cursor.execute("SELECT id, student_id, session_id, full_name, email, score FROM surveys_module5submission ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows:
    print(dict(row))

print("\n=== surveys_module6submission ===")
cursor.execute("SELECT id, student_id, session_id, full_name, email, score FROM surveys_module6submission ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows:
    print(dict(row))

print("\n=== surveys_module7submission ===")
cursor.execute("SELECT id, student_id, session_id, full_name, email, score FROM surveys_module7submission ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows:
    print(dict(row))

print("\n=== surveys_formpresence ===")
cursor.execute("SELECT id, student_id, module_code, training_session_id, status FROM surveys_formpresence ORDER BY id")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for row in rows[:5]:
    print(dict(row))
if len(rows) > 5:
    print(f"  ... and {len(rows)-5} more")

conn.close()
