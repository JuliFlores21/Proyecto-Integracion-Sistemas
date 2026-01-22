#!/bin/bash

# This script creates multiple databases if provided
# POSTGRES_USER and POSTGRES_DB are standard env vars used by the image for the default DB.
# We add creation for the Analytics DB.

set -e
set -u

function create_user_and_database() {
	local database=$1
	echo "  Creating user and database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "${DB_NAME_ANALYTICS:-}" ]; then
	create_user_and_database $DB_NAME_ANALYTICS
fi
