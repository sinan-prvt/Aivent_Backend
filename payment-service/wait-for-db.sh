#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "Waiting for PostgreSQL at $host:$port ..."
  sleep 1
done

>&2 echo "Postgres is up. Enable Watch"

if [ -n "$cmd" ]; then
    exec $cmd
fi
