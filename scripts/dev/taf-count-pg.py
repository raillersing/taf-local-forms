#!/usr/bin/env python3
"""Count records in PostgreSQL via Django ORM."""
import os, sys
sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()
from django.conf import settings

db = settings.DATABASES["default"]
assert "postgresql" in db["ENGINE"], f"Not PostgreSQL: {db['ENGINE']}"

from surveys.models import (
    TrainingModule, TrainingSession, Student,
    Submission, Module3Submission, Module4Submission,
    Module5Submission, Module6Submission, Module7Submission,
    FormPresence,
)
from django.contrib.auth import get_user_model

User = get_user_model()
models = {
    "surveys_trainingmodule": TrainingModule,
    "surveys_trainingsession": TrainingSession,
    "surveys_student": Student,
    "surveys_submission": Submission,
    "surveys_module3submission": Module3Submission,
    "surveys_module4submission": Module4Submission,
    "surveys_module5submission": Module5Submission,
    "surveys_module6submission": Module6Submission,
    "surveys_module7submission": Module7Submission,
    "surveys_formpresence": FormPresence,
    "auth_user": User,
}

print(f"PostgreSQL DB: {db['NAME']} on {db['HOST']}:{db['PORT']}")
print("=" * 50)
for name, model in models.items():
    count = model.objects.count()
    print(f"  {name}: {count}")
