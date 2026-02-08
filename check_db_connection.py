import os
import sys
import psycopg2
from urllib.parse import urlparse

# Force the URL provided by user
DATABASE_URL = "postgresql://postgres:Xazrat_ali571@db.rvboscxljclteqvlxmeo.supabase.co:5432/postgres"

print(f"Testing connection to: {DATABASE_URL.split('@')[-1]}") # Hide password in logs

try:
    # 1. Test DNS Resolution
    result = urlparse(DATABASE_URL)
    hostname = result.hostname
    print(f"Resolving hostname: {hostname}...")
    import socket
    ip = socket.gethostbyname(hostname)
    print(f"DNS Success: {hostname} -> {ip}")

    # 2. Test Connection
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
    print("✅ Connection SUCCESS!")
    conn.close()
except socket.gaierror as e:
    print(f"❌ DNS Error: Could not resolve hostname '{hostname}'.")
    print("   Make sure the Project ID 'rvboscxljclteqvlxmeo' is correct and project is active.")
except psycopg2.OperationalError as e:
    print(f"❌ Connection Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
