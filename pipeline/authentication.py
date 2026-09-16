import hashlib


# --------------------------------------------------
# USER DATABASE
# --------------------------------------------------

users = {
    "admin": {
        "password": "admin123",
        "role": "Admin"
    },
    "officer": {
        "password": "officer123",
        "role": "Civic Officer"
    },
    "citizen": {
        "password": "citizen123",
        "role": "Citizen"
    }
}


# --------------------------------------------------
# PASSWORD HASHING
# --------------------------------------------------

def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# Create hashed passwords
for username in users:
    users[username]["password"] = hash_password(
        users[username]["password"]
    )


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def authenticate(username, password):

    if username not in users:
        return None

    hashed_password = hash_password(password)

    if users[username]["password"] == hashed_password:
        return users[username]["role"]

    return None


# --------------------------------------------------
# ROLE-BASED ACCESS CONTROL
# --------------------------------------------------

permissions = {
    "Admin": [
        "view_all_data",
        "manage_users",
        "manage_system",
        "view_predictions"
    ],

    "Civic Officer": [
        "view_ward_data",
        "view_complaints",
        "view_predictions"
    ],

    "Citizen": [
        "submit_complaint",
        "view_own_complaints",
        "view_public_data"
    ]
}


def check_permission(role, permission):

    if role not in permissions:
        return False

    return permission in permissions[role]


# --------------------------------------------------
# TEST LOGIN
# --------------------------------------------------

print("UrbanSim Civic AI - Authentication Test")
print("-----------------------------------------")

username = input("Enter username: ").strip()
password = input("Enter password: ")

role = authenticate(username, password)

if role:

    print()
    print("Authentication successful!")
    print(f"Role: {role}")

    print()
    print("Available permissions:")

    for permission in permissions[role]:
        print(f"- {permission}")

else:

    print()
    print("Authentication failed!")
    print("Invalid username or password.")