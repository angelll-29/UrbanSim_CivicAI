import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 70)
print("       URBANSIM CIVIC AI -- BACKEND AUTHENTICATION & RBAC TEST        ")
print("=" * 70)

# 1. Health check
res = client.get('/api/health')
print('1. Health check:', res.status_code, res.json())
assert res.status_code == 200

# 2. Seed users
res = client.get('/api/auth/seed-users')
seed_users = res.json()
print(f'2. Seed users available: {len(seed_users)}')
for s in seed_users:
    print(f"   - {s['username']:<10} | Role: {s['role']:<16} | Email: {s['email']}")

# 3. Test Invalid Login
res = client.post('/api/auth/login', json={'username': 'citizen', 'password': 'wrongpassword'})
print(f'3. Invalid login response: {res.status_code} (Expected 401)')
assert res.status_code == 401

# 4. Test Valid Logins for all 4 roles
roles = ['citizen', 'analyst', 'authority', 'admin']
tokens = {}
for u in roles:
    res = client.post('/api/auth/login', json={'username': u, 'password': f'{u}123'})
    assert res.status_code == 200, f'Login failed for {u}: {res.text}'
    data = res.json()
    tokens[u] = data['access_token']
    role = data['user']['role']
    print(f"4. Login [{u}] -> Role: {role} -> Token: {tokens[u][:20]}...")

# 5. Test /api/auth/me
headers_citizen = {'Authorization': f'Bearer {tokens["citizen"]}'}
res = client.get('/api/auth/me', headers=headers_citizen)
assert res.status_code == 200
print(f"5. Citizen profile verified: {res.json()['name']} ({res.json()['role']})")

# 6. Test Protected Admin Route with Citizen (Expected 403 Forbidden)
res = client.get('/api/auth/admin/users', headers=headers_citizen)
print(f"6. Citizen accessing /admin/users: {res.status_code} (Expected 403 Forbidden)")
assert res.status_code == 403

# 7. Test Protected Admin Route with Analyst (Expected 403 Forbidden)
headers_analyst = {'Authorization': f'Bearer {tokens["analyst"]}'}
res = client.get('/api/auth/admin/users', headers=headers_analyst)
print(f"7. Analyst accessing /admin/users: {res.status_code} (Expected 403 Forbidden)")
assert res.status_code == 403

# 8. Test Protected Admin Route with Authority (Expected 403 Forbidden)
headers_authority = {'Authorization': f'Bearer {tokens["authority"]}'}
res = client.get('/api/auth/admin/users', headers=headers_authority)
print(f"8. Authority accessing /admin/users: {res.status_code} (Expected 403 Forbidden)")
assert res.status_code == 403

# 9. Test Protected Admin Route with Admin (Expected 200 OK)
headers_admin = {'Authorization': f'Bearer {tokens["admin"]}'}
res = client.get('/api/auth/admin/users', headers=headers_admin)
assert res.status_code == 200
print(f"9. Admin accessing /admin/users: {res.status_code} (Found {len(res.json())} users)")

# 10. Test System Stats
res = client.get('/api/auth/admin/system-stats', headers=headers_admin)
assert res.status_code == 200
print(f"10. Admin accessing /admin/system-stats: {res.status_code} (Status: {res.json()['status']})")

# 11. Test Audit Logs
res = client.get('/api/auth/admin/audit-logs', headers=headers_admin)
assert res.status_code == 200
logs = res.json()
print(f"11. Audit logs recorded: {len(logs)} entries")
if logs:
    latest = logs[0]
    print(f"    Latest: {latest['timestamp']} | User: {latest['user']} | Action: {latest['action']} | Status: {latest['status']}")

print("=" * 70)
print("[SUCCESS] ALL 11 BACKEND AUTH & RBAC SECURITY TESTS PASSED!")
print("=" * 70)
