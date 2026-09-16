from pathlib import Path
from datetime import datetime

# Log file
log_file = Path("logs/audit.log")

# Make sure logs folder exists
log_file.parent.mkdir(parents=True, exist_ok=True)


def log_event(username, role, action, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"{timestamp} | "
        f"User: {username} | "
        f"Role: {role} | "
        f"Action: {action} | "
        f"Status: {status}\n"
    )

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(log_entry)


# --------------------------------------------------
# DEMONSTRATION
# --------------------------------------------------

print("UrbanSim Civic AI - Audit Logging")
print("----------------------------------")

log_event(
    "admin",
    "Admin",
    "Viewed all urban data",
    "SUCCESS"
)

log_event(
    "officer",
    "Civic Officer",
    "Viewed ward complaints",
    "SUCCESS"
)

log_event(
    "citizen",
    "Citizen",
    "Submitted complaint",
    "SUCCESS"
)

log_event(
    "unknown_user",
    "Unknown",
    "Attempted unauthorized access",
    "FAILED"
)

print("Audit events recorded successfully!")
print(f"Audit log saved to: {log_file}")