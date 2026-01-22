import time
import os
import psycopg2

DB_URL = os.getenv("DATABASE_URL")

print("⏳ Waiting for database...")

for i in range(30):  # wait up to ~30 seconds
    try:
        conn = psycopg2.connect(DB_URL)
        conn.close()
        print("✅ Database is ready")
        break
    except Exception as e:
        print(f"⏳ DB not ready yet ({i+1}/30)")
        time.sleep(1)
else:
    raise RuntimeError("❌ Database not ready after 30 seconds")
