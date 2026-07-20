import psycopg2
import time

url = "postgresql://database_url_s4qc_user:mmGQDQ0eQ43ogsiIS7V68gD8fRyBLIqZ@dpg-d9cfji1kh4rs73cn0ca0-a.singapore-postgres.render.com/database_url_s4qc?sslmode=require"

for i in range(12):
    print(f"Attempt {i+1} to connect...")
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        print("Success! Connection established.")
        conn.close()
        break
    except Exception as e:
        print(f"Failed: {e}")
        time.sleep(5)
