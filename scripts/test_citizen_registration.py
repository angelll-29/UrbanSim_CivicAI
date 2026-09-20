import os
import sys
import sqlite3
from datetime import datetime

# Add project root to sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import DB_PATH, get_db_connection, list_all_users

client = TestClient(app)

def run_registration_tests():
    print("=" * 70)
    print("      URBANSIM CIVIC AI -- CITIZEN REGISTRATION & DATABASE TEST       ")
    print("=" * 70)

    # 1. Verify SQLite Database File Exists
    print(f"1. Database path: {DB_PATH}")
    assert os.path.exists(DB_PATH), "SQLite database file was not created!"
    print("   [+] Database file exists.")

    # 2. Count current users in database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM users")
    initial_count = c.fetchone()["cnt"]
    print(f"2. Current users in SQLite DB: {initial_count}")
    conn.close()

    # 3. Register a brand new Citizen
    test_username = f"priya_mumbai_{int(datetime.now().timestamp())}"
    test_email = f"{test_username}@example.com"
    test_password = "SecurePassword123"

    payload = {
        "name": "Priya Deshmukh",
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "ward": "KW",
        "phone": "+91 98200 55443",
        "address": "Lokhandwala Complex, Andheri West"
    }

    print(f"3. Registering new citizen: {test_username} (Ward: KW)...")
    reg_res = client.post("/api/auth/register", json=payload)
    print(f"   Status: {reg_res.status_code}")
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"

    data = reg_res.json()
    assert "access_token" in data, "No access token in registration response!"
    assert data["user"]["role"] == "CITIZEN", "Registered user role must be CITIZEN!"
    assert data["user"]["ward"] == "KW", "Ward must match KW!"
    print(f"   [+] Registered citizen token: {data['access_token'][:25]}...")
    print(f"   [+] Profile: {data['user']['name']} (@{data['user']['username']}) | Role: {data['user']['role']} | Ward: {data['user']['ward']}")

    # 4. Verify Record in SQLite Database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (test_username,))
    db_row = c.fetchone()
    conn.close()

    assert db_row is not None, "Citizen record not found in SQLite database!"
    assert db_row["email"] == test_email, "Email in database does not match!"
    assert db_row["role"] == "CITIZEN", "Role in database does not match!"
    assert db_row["ward"] == "KW", "Ward in database does not match!"
    print(f"4. Verified SQLite Row:")
    print(f"   ID: {db_row['id']} | Name: {db_row['name']} | Email: {db_row['email']} | Ward: {db_row['ward']} | Created: {db_row['created_at']}")

    # 5. Test Login with Newly Created Citizen Credentials
    print(f"5. Testing login with new credentials ({test_username})...")
    login_res = client.post("/api/auth/login", json={"username": test_username, "password": test_password})
    assert login_res.status_code == 200, f"Login failed for new citizen: {login_res.text}"
    login_data = login_res.json()
    assert login_data["user"]["username"] == test_username
    print(f"   [+] Login successful with verified token: {login_data['access_token'][:25]}...")

    # 6. Test Duplicate Registration Protection
    print("6. Testing duplicate username rejection...")
    dup_res = client.post("/api/auth/register", json=payload)
    assert dup_res.status_code == 400, "Duplicate registration should return 400 Bad Request!"
    print(f"   [+] Duplicate properly rejected with 400 Bad Request: {dup_res.json()['detail']}")

    print("=" * 70)
    print("[SUCCESS] ALL CITIZEN REGISTRATION & SQLITE DATABASE TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_registration_tests()
