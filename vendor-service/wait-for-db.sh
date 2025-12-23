#!/bin/sh
set -e

HOST="$1"
PORT="$2"
shift 2

echo "Waiting for PostgreSQL at $HOST:$PORT ..."

until nc -z "$HOST" "$PORT"; do
  echo "Postgres not ready yet..."
  sleep 2
done

echo "Postgres is up."
exec "$@"
