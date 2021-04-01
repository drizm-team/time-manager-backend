#!/bin/bash
export DJANGO_SETTINGS_MODULE=TimeManagerBackend.settings.production
source "$(dirname "$0")"/common.sh

db_setting_path="DATABASES['default']"
settings=(
  "CLOUD_SQL_CONN_NAME"
  "${db_setting_path}['NAME']"
  "${db_setting_path}['USER']"
  "${db_setting_path}['PASSWORD']"
)

for index in "${!settings[@]}"; do
  setting_name=${settings[$index]}
  settings[$index]="$(django_settings "$setting_name")"
done

~/cloud_sql_proxy -instances="${settings[0]}"=tcp:5432 &
pid=$!
# Give the proxy some time to connect
sleep 5

query="GRANT pg_signal_backend TO ${settings[2]};
       SELECT pg_terminate_backend(pid), * FROM pg_stat_activity
       WHERE usename = '${settings[2]}' AND pid <> pg_backend_pid();
       DROP DATABASE \"${settings[1]}\";
       CREATE DATABASE \"${settings[1]}\" OWNER \"${settings[2]}\";"

psql --echo-errors "postgresql://${settings[2]}:${settings[3]}@localhost/postgres" << EOF
       $query
EOF

kill $pid
exit 0
