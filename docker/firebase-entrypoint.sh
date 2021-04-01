#!/bin/bash
set -eu

if [ "${ENV_TEST:-1}" == 1 ]; then
	# We do not want to persist data when we are running tests
	firebase \
	  --non-interactive -c /firebase.json --token "$(cat /.firebasekey)" \
	  emulators:start
else
	firebase \
	  --non-interactive -c /firebase.json --token "$(cat /.firebasekey)" \
	  emulators:start --import=/firestore-data --export-on-exit
fi
