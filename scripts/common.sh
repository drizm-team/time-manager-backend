#!/bin/bash

join() {
    local retname=$1 sep=$2 values=$3
    shift 3 || shift $(($#))
    printf -v "$retname" "%s" "$values${*/#/$sep}"
}


django_settings() {
  local setting=$1
  if [[ $setting == *"["* ]]; then
    IFS='[' read -ra keys_split <<< "${setting#*\[}"
    keys=()
    for i in "${!keys_split[@]}"; do
      key=${keys_split[$i]}
      if [ -n "$key" ]; then
        key=${key::-1}
        if [[ $key != *"'"* ]]; then
          key="'${key}'"
        fi
        keys+=("[${key}]")
      fi
    done
    join keys "" "${keys[@]}"
    # shellcheck disable=SC2128
    setting="${setting%%[*}${keys}"
  fi
  local command="from django.conf import settings; print(settings.${setting})"
  # shellcheck disable=SC2155
  local result=$(poetry run python -c "${command}")
  echo "$result"
}
