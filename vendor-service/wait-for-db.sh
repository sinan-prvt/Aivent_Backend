HOST=${1:-vendor_db}
PORT=${2:-5432}

echo "Waiting for PostgreSQL at ${HOST}:${PORT} ..."

if command -v nc >/dev/null 2>&1; then
  while ! nc -z ${HOST} ${PORT}; do
    echo "Postgres not ready yet..."
    sleep 1
  done
else
  while ! (echo > /dev/tcp/${HOST}/${PORT}) 2>/dev/null; do
    echo "Postgres not ready yet..."
    sleep 1
  done
fi

echo "Postgres at ${HOST}:${PORT} is available"
