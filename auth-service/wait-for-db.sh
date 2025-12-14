host="$1"
port="$2"

echo "Waiting for PostgreSQL at $host:$port ..."

while ! nc -z "$host" "$port"; do
  echo "Postgres not ready yet..."
  sleep 2
done

echo "Postgres is up."
