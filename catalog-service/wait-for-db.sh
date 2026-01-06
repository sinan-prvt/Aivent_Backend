#!/bin/sh
set -e

HOST="$1"
PORT="$2"
shift 2

echo "Waiting for PostgreSQL at $HOST:$PORT ..."

until python -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('$HOST', int('$PORT'))); s.close()" 2>/dev/null; do
  echo "Postgres not ready yet..."
  sleep 2
done

echo "Postgres is up."
exec "$@"
