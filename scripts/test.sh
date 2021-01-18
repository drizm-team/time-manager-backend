poetry shell

tests_config=(
  "PYTHONUNBUFFERED=1"
  "DJANGO_SETTINGS_MODULE=TimeManagerBackend.settings.development"
)
dir="tests"

for e in "${tests_config[@]}"; do
  eval "export ${e}"
done

firebase emulators:exec --only firestore "python manage.py test $dir"
