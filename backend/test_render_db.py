import psycopg2
import sys

regions = [
    "oregon-postgres.render.com",
    "ohio-postgres.render.com",
    "frankfurt-postgres.render.com",
    "singapore-postgres.render.com"
]

user = "database_url_s4qc_user"
password = "mmGQDQ0eQ43ogsiIS7V68gD8fRyBLIqZ"
dbname = "database_url_s4qc"
prefix = "dpg-d9cfji1kh4rs73cn0ca0-a"

for region in regions:
    host = f"{prefix}.{region}"
    print(f"Trying {host}...")
    try:
        conn = psycopg2.connect(
            host=host,
            database=dbname,
            user=user,
            password=password,
            connect_timeout=5,
            sslmode="require"
        )
        print(f"Success! The region is {region}")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"Failed: {e}")

print("Could not connect to any region.")
sys.exit(1)
