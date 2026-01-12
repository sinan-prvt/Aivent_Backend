#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
shift
cmd="$@"

until nc -z "$host" 5432; do
  >&2 echo "Waiting for PostgreSQL at $host:5432 ..."
  sleep 1
done

>&2 echo "Postgres is up. Enable Watch"
exec $cmd
