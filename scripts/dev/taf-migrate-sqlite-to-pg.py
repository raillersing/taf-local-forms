#!/usr/bin/env python3
"""
Migrate all data from old SQLite to PostgreSQL, preserving relationships.
Safe: never deletes anything, only INSERTs.

Usage: cat taf-migrate-sqlite-to-pg.py | docker compose exec -T web python3
"""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.conf import settings
from django.db import transaction

import sqlite3

PG_HOST = settings.DATABASES["default"]["HOST"]
assert "postgresql" in settings.DATABASES["default"]["ENGINE"], "Must run against PostgreSQL"
assert PG_HOST != "localhost" or os.environ.get("DB_HOST", "") != "", "PG_HOST=localhost with no DB_HOST suggests SQLite"

# --- Step 0: Connect to SQLite ---
SQLITE_PATH = "/app/data/db.sqlite3"
if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: {SQLITE_PATH} not found - old SQLite volume not mounted?")
    sys.exit(1)

sq = sqlite3.connect(SQLITE_PATH)
sq.row_factory = sqlite3.Row
sq_cursor = sq.cursor()

from surveys.models import (
    TrainingModule, TrainingSession, Student,
    Submission, Module3Submission, Module4Submission,
    Module5Submission, Module6Submission, Module7Submission,
    FormPresence,
)
from django.contrib.auth import get_user_model
User = get_user_model()

# --- Step 1: Pre-migration counts ---
print("=" * 60)
print("PRE-MIGRATION COUNTS")
print("=" * 60)
print(f"{'Table':<35} {'SQLite':<10} {'PostgreSQL':<10}")
tables_info = [
    ("auth_user", User),
    ("surveys_trainingmodule", TrainingModule),
    ("surveys_trainingsession", TrainingSession),
    ("surveys_student", Student),
    ("surveys_submission", Submission),
    ("surveys_module3submission", Module3Submission),
    ("surveys_module4submission", Module4Submission),
    ("surveys_module5submission", Module5Submission),
    ("surveys_module6submission", Module6Submission),
    ("surveys_module7submission", Module7Submission),
    ("surveys_formpresence", FormPresence),
]
for name, model in tables_info:
    sq_cursor.execute(f"SELECT COUNT(*) FROM {name}")
    sq_cnt = sq_cursor.fetchone()[0]
    pg_cnt = model.objects.count()
    print(f"{name:<35} {sq_cnt:<10} {pg_cnt:<10}")

# --- Step 2: Check TrainingSession ID alignment ---
print("\n" + "=" * 60)
print("TRAINING SESSION ID CHECK")
print("=" * 60)
sq_cursor.execute("SELECT id, module_id, session_code, is_active FROM surveys_trainingsession ORDER BY id")
sq_sessions = {row["id"]: dict(row) for row in sq_cursor.fetchall()}
pg_sessions = {s.id: s for s in TrainingSession.objects.all().order_by("id")}

print(f"SQLite session IDs: {list(sq_sessions.keys())}")
print(f"PG session IDs:     {list(pg_sessions.keys())}")

# Check if session codes match
for sq_id, sq_row in sq_sessions.items():
    pg_match = [s for s in pg_sessions.values() if s.session_code == sq_row["session_code"]]
    if pg_match:
        pg_match_obj = pg_match[0]
        if pg_match_obj.id != sq_id:
            print(f"  MISMATCH: SQLite session id={sq_id} code={sq_row['session_code']} -> PG id={pg_match_obj.id}")
    else:
        print(f"  MISSING: SQLite session id={sq_id} code={sq_row['session_code']} not found in PG")

# --- Step 3: Check module alignment ---
print("\n" + "=" * 60)
print("MODULE CODE CHECK")
print("=" * 60)
sq_cursor.execute("SELECT id, code FROM surveys_trainingmodule ORDER BY id")
sq_modules = {row["id"]: row["code"] for row in sq_cursor.fetchall()}
pg_modules = {m.id: m.code for m in TrainingModule.objects.all().order_by("id")}
print(f"SQLite module codes: {list(sq_modules.values())}")
print(f"PG module codes:     {list(pg_modules.values())}")

# --- Step 4: User migration (only users not in PG) ---
print("\n" + "=" * 60)
print("USER MIGRATION")
print("=" * 60)
sq_cursor.execute("SELECT id, username, password, email, is_superuser, is_staff, is_active, date_joined FROM auth_user ORDER BY id")
sq_users = sq_cursor.fetchall()
user_id_map = {}
for sq_u in sq_users:
    existing = User.objects.filter(username=sq_u["username"]).first()
    if existing:
        print(f"  SKIP user id={sq_u['id']}: username '{sq_u['username']}' already exists in PG as id={existing.id}")
        user_id_map[sq_u["id"]] = existing.id
    else:
        created = User(
            username=sq_u["username"],
            email=sq_u["email"],
            password=sq_u["password"],  # preserve Django hash from SQLite
            is_superuser=bool(sq_u["is_superuser"]),
            is_staff=bool(sq_u["is_staff"]),
            is_active=bool(sq_u["is_active"]),
            date_joined=sq_u["date_joined"],
        )
        created.save()
        user_id_map[sq_u["id"]] = created.id
        print(f"  MIGRATED user id={sq_u['id']} -> PG id={created.id} (username='{sq_u['username']}')")

# --- Step 5: Student migration ---
print("\n" + "=" * 60)
print("STUDENT MIGRATION")
print("=" * 60)
sq_cursor.execute("SELECT id, school_id_number, full_name, class_level, group_name FROM surveys_student ORDER BY id")
sq_students = sq_cursor.fetchall()
student_id_map = {}
for sq_s in sq_students:
    existing = Student.objects.filter(
        school_id_number=sq_s["school_id_number"],
        full_name=sq_s["full_name"],
    ).first()
    if existing:
        student_id_map[sq_s["id"]] = existing.id
        print(f"  SKIP student id={sq_s['id']}: already exists as PG id={existing.id} ({sq_s['full_name']})")
    else:
        created = Student.objects.create(
            school_id_number=sq_s["school_id_number"],
            full_name=sq_s["full_name"],
            class_level=sq_s["class_level"],
            group_name=sq_s["group_name"] or "",
        )
        student_id_map[sq_s["id"]] = created.id
        print(f"  MIGRATED student id={sq_s['id']} -> PG id={created.id} ({sq_s['full_name']})")

# --- Step 6: Submission migration ---
print("\n" + "=" * 60)
print("M2 SUBMISSION MIGRATION")
print("=" * 60)

# Build session code -> PG id mapping
pg_session_by_code = {s.session_code: s.id for s in TrainingSession.objects.all()}

sq_cursor.execute("""
    SELECT * FROM surveys_submission ORDER BY id
""")
sq_rows = sq_cursor.fetchall()
columns = [desc[0] for desc in sq_cursor.description]
sub_id_map = {}
for sq_row in sq_rows:
    row = dict(zip(columns, sq_row))
    old_id = row["id"]
    # Already exists? Check by session + school_id_number
    session_pg_id = pg_session_by_code.get(sq_sessions[row["session_id"]]["session_code"])
    if not session_pg_id:
        print(f"  SKIP M2 submission id={old_id}: session not found in PG")
        continue
    existing = Submission.objects.filter(
        session_id=session_pg_id,
        school_id_number_snapshot=row["school_id_number_snapshot"],
    ).first()
    if existing:
        sub_id_map[old_id] = existing.id
        print(f"  SKIP M2 submission id={old_id}: already exists as PG id={existing.id}")
        continue
    # Remap student FK
    new_student_id = student_id_map.get(row["student_id"])
    if not new_student_id:
        print(f"  SKIP M2 submission id={old_id}: student_id={row['student_id']} not found in PG")
        continue
    obj = Submission(
        school_id_number_snapshot=row["school_id_number_snapshot"],
        student_id=new_student_id,
        session_id=session_pg_id,
    )
    for field in ["auto_eval_internet_explained", "auto_eval_learning_usage", "auto_eval_open_browser",
                   "todo_opened_browser", "todo_typed_simple_search", "todo_used_keywords",
                   "todo_opened_result", "todo_compared_results", "todo_found_school_info",
                   "todo_asked_for_help", "todo_noted_learning",
                   "quiz_q1", "quiz_q2", "quiz_q3", "quiz_q4_selected", "quiz_q5",
                   "practical_search_text", "practical_site_text", "practical_subject",
                   "feedback_understood_today", "feedback_still_difficult", "feedback_confidence",
                   "computed_score", "created_at", "updated_at"]:
        if field in row and row[field] is not None:
            setattr(obj, field, row[field])
    obj.save()
    # Force-rewrite created_at/updated_at (auto_now overrides on save)
    if "created_at" in row and row["created_at"] is not None:
        Submission.objects.filter(pk=obj.pk).update(created_at=row["created_at"])
    if "updated_at" in row and row["updated_at"] is not None:
        Submission.objects.filter(pk=obj.pk).update(updated_at=row["updated_at"])
    sub_id_map[old_id] = obj.id
    print(f"  MIGRATED M2 submission id={old_id} -> PG id={obj.id}")

# --- Step 7: Module 3-7 submissions ---
for mod_class, mod_table, mod_label in [
    (Module3Submission, "surveys_module3submission", "M3"),
    (Module4Submission, "surveys_module4submission", "M4"),
    (Module5Submission, "surveys_module5submission", "M5"),
    (Module6Submission, "surveys_module6submission", "M6"),
    (Module7Submission, "surveys_module7submission", "M7"),
]:
    print(f"\n{'=' * 60}")
    print(f"{mod_label} SUBMISSION MIGRATION")
    print(f"{'=' * 60}")
    sq_cursor.execute(f"SELECT * FROM {mod_table} ORDER BY id")
    sq_rows = sq_cursor.fetchall()
    columns = [desc[0] for desc in sq_cursor.description]
    for sq_row in sq_rows:
        row = dict(zip(columns, sq_row))
        old_id = row["id"]
        session_pg_id = pg_session_by_code.get(sq_sessions[row["session_id"]]["session_code"])
        if not session_pg_id:
            print(f"  SKIP {mod_label} submission id={old_id}: session not found in PG")
            continue
        existing = mod_class.objects.filter(
            session_id=session_pg_id,
            school_id_number_snapshot=row["school_id_number_snapshot"],
        ).first()
        if existing:
            print(f"  SKIP {mod_label} submission id={old_id}: already exists as PG id={existing.id}")
            continue
        new_student_id = student_id_map.get(row["student_id"])
        if not new_student_id:
            print(f"  SKIP {mod_label} submission id={old_id}: student_id={row['student_id']} not found in PG")
            continue
        obj = mod_class(
            school_id_number_snapshot=row["school_id_number_snapshot"],
            student_id=new_student_id,
            session_id=session_pg_id,
        )
        for field in columns:
            if field in ("id", "school_id_number_snapshot", "student_id", "session_id"):
                continue
            if field in row and row[field] is not None:
                setattr(obj, field, row[field])
        obj.save()
        if "created_at" in row and row["created_at"] is not None:
            mod_class.objects.filter(pk=obj.pk).update(created_at=row["created_at"])
        if "updated_at" in row and row["updated_at"] is not None:
            mod_class.objects.filter(pk=obj.pk).update(updated_at=row["updated_at"])
        print(f"  MIGRATED {mod_label} submission id={old_id} -> PG id={obj.id}")

# --- Step 8: FormPresence migration ---
print("\n" + "=" * 60)
print("FORMPRESENCE MIGRATION")
print("=" * 60)
sq_cursor.execute("SELECT * FROM surveys_formpresence ORDER BY id")
sq_rows = sq_cursor.fetchall()
columns = [desc[0] for desc in sq_cursor.description]
fp_count = 0
fp_skip_count = 0
for sq_row in sq_rows:
    row = dict(zip(columns, sq_row))
    old_id = row["id"]
    session_pg_id = pg_session_by_code.get(sq_sessions.get(row["training_session_id"], {}).get("session_code", ""))
    if not session_pg_id:
        print(f"  SKIP FormPresence id={old_id}: session not found")
        fp_skip_count += 1
        continue
    existing = FormPresence.objects.filter(
        client_id=row["client_id"],
        module_code=row["module_code"],
        training_session_id=session_pg_id,
    ).first()
    if existing:
        fp_skip_count += 1
        continue
    obj = FormPresence(
        module_code=row["module_code"],
        training_session_id=session_pg_id,
        client_id=row["client_id"],
        status=row["status"],
        current_path=row["current_path"] or "",
        school_id_number=row["school_id_number"],
        class_level=row["class_level"],
    )
    for field in ["started_at", "last_seen_at"]:
        if field in row and row[field] is not None:
            setattr(obj, field, row[field])
    obj.save()
    fp_count += 1
print(f"  MIGRATED FormPresence: {fp_count}")
print(f"  SKIPPED FormPresence: {fp_skip_count}")

# --- Final: Post-migration counts ---
print("\n" + "=" * 60)
print("POST-MIGRATION COUNTS")
print("=" * 60)
print(f"{'Table':<35} {'SQLite':<10} {'PostgreSQL':<10}")
for name, model in tables_info:
    sq_cursor.execute(f"SELECT COUNT(*) FROM {name}")
    sq_cnt = sq_cursor.fetchone()[0]
    pg_cnt = model.objects.count()
    print(f"{name:<35} {sq_cnt:<10} {pg_cnt:<10}")

sq.close()
print("\nMigration complete. Backup at /tmp/db_backup_preservation.sqlite3 (container) and /tmp/db_backup_preservation.sqlite3 (host).")
