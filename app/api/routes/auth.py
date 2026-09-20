import os
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import (
    USERS_DB,
    PERMISSIONS,
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    require_roles,
    log_audit_event,
    AUDIT_LOG_FILE
)
from app.db.database import (
    get_user_by_username_or_email,
    create_citizen_in_db,
    list_all_users,
    get_user_counts_by_role
)

router = APIRouter()

# --------------------------------------------------
# SCHEMAS
# --------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class CitizenRegisterRequest(BaseModel):
    username: str
    email: str
    name: str
    password: str
    ward: Optional[str] = "GS"
    phone: Optional[str] = None
    address: Optional[str] = None

class UserCreateRequest(BaseModel):
    username: str
    email: str
    name: str
    password: str
    role: str
    ward: Optional[str] = "All"

class UserResponse(BaseModel):
    username: str
    email: str
    name: str
    role: str
    ward: str
    phone: Optional[str] = None
    permissions: List[str]

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --------------------------------------------------
# AUTH & REGISTRATION ROUTES
# --------------------------------------------------

@router.post("/register", response_model=LoginResponse)
@router.post("/signup", response_model=LoginResponse)
def register_citizen(payload: CitizenRegisterRequest):
    """
    Real Citizen Self-Registration:
    Stores the citizen record persistently into the SQLite database (`data/urbansim_users.db`),
    records an audit event, and returns a valid JWT authentication session.
    """
    clean_username = payload.username.strip().lower()
    clean_email = payload.email.strip().lower()
    clean_name = payload.name.strip()
    clean_password = payload.password.strip()
    ward_code = (payload.ward or "GS").strip().upper()

    if len(clean_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long."
        )

    if len(clean_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    if "@" not in clean_email or "." not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address."
        )

    try:
        new_citizen = create_citizen_in_db(
            username=clean_username,
            email=clean_email,
            name=clean_name,
            password=clean_password,
            ward=ward_code,
            phone=payload.phone,
            address=payload.address
        )
    except ValueError as val_err:
        log_audit_event(
            clean_username,
            "CITIZEN",
            "Citizen self-registration failed",
            "FAILED",
            str(val_err)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

    # Issue JWT Token
    role = "CITIZEN"
    permissions = PERMISSIONS.get(role, [])
    access_token = create_access_token(
        data={
            "sub": new_citizen["username"],
            "role": role,
            "permissions": permissions
        }
    )

    log_audit_event(
        new_citizen["username"],
        role,
        f"Citizen self-registered in Ward {ward_code} and stored in database",
        "SUCCESS"
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            username=new_citizen["username"],
            email=new_citizen["email"],
            name=new_citizen["name"],
            role=role,
            ward=new_citizen["ward"],
            phone=new_citizen.get("phone"),
            permissions=permissions
        )
    )

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    username_or_email = payload.username.strip().lower()
    password = payload.password.strip()

    # 1. Lookup in SQLite database
    user_record = get_user_by_username_or_email(username_or_email)

    # 2. Fallback to memory seed if needed
    if not user_record:
        for u in USERS_DB.values():
            if u["username"].lower() == username_or_email or u["email"].lower() == username_or_email:
                user_record = {
                    "username": u["username"],
                    "email": u["email"],
                    "name": u["name"],
                    "password_hash": u["password"],
                    "role": u["role"],
                    "ward": u.get("ward", "All"),
                    "is_active": u.get("is_active", True)
                }
                break

    pwd_hash = user_record.get("password_hash") if user_record else None
    if not user_record or not pwd_hash or not verify_password(password, pwd_hash):
        log_audit_event(
            payload.username, 
            "UNKNOWN", 
            "Login attempt", 
            "FAILED", 
            "Invalid username or password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_record.get("is_active", 1):
        log_audit_event(
            user_record["username"], 
            user_record["role"], 
            "Login attempt", 
            "DENIED", 
            "Account deactivated"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Issue JWT Token
    role = user_record["role"]
    permissions = PERMISSIONS.get(role, [])
    access_token = create_access_token(
        data={
            "sub": user_record["username"],
            "role": role,
            "permissions": permissions
        }
    )

    log_audit_event(
        user_record["username"], 
        role, 
        "User authenticated successfully", 
        "SUCCESS"
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            username=user_record["username"],
            email=user_record["email"],
            name=user_record["name"],
            role=role,
            ward=user_record.get("ward", "All"),
            phone=user_record.get("phone"),
            permissions=permissions
        )
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(**current_user)

@router.post("/logout")
def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    log_audit_event(
        current_user["username"], 
        current_user["role"], 
        "User logged out", 
        "SUCCESS"
    )
    return {"message": "Logged out successfully"}

@router.get("/seed-users")
def get_seed_users():
    """Development helper returning available demo roles and accounts"""
    return [
        {
            "username": u["username"],
            "name": u["name"],
            "role": u["role"],
            "email": u["email"],
            "sample_password": f"{u['username']}123",
            "description": {
                "CITIZEN": "Public participation, ward discovery & civic complaints",
                "URBAN_ANALYST": "Full analytical GIS, deep learning models & scenarios",
                "URBAN_AUTHORITY": "Operational city command, complaint queues & oversight",
                "SYSTEM_ADMIN": "System settings, users, audit logs & model infrastructure"
            }.get(u["role"], "")
        }
        for u in USERS_DB.values()
    ]

# --------------------------------------------------
# SYSTEM ADMIN PROTECTED ROUTES
# --------------------------------------------------
@router.get("/admin/users", dependencies=[Depends(require_roles(["SYSTEM_ADMIN"]))])
def list_users_admin():
    db_users = list_all_users()
    return [
        {
            "id": u.get("id"),
            "username": u["username"],
            "email": u["email"],
            "name": u["name"],
            "role": u["role"],
            "ward": u.get("ward", "All"),
            "phone": u.get("phone"),
            "is_active": bool(u.get("is_active", 1)),
            "created_at": u.get("created_at")
        }
        for u in db_users
    ]

@router.post("/admin/users", dependencies=[Depends(require_roles(["SYSTEM_ADMIN"]))])
def create_user_admin(payload: UserCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    if payload.role not in PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed roles: {list(PERMISSIONS.keys())}"
        )

    try:
        new_u = create_citizen_in_db(
            username=payload.username,
            email=payload.email,
            name=payload.name,
            password=payload.password,
            ward=payload.ward or "All"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    log_audit_event(
        current_user["username"], 
        current_user["role"], 
        f"Admin created user '{payload.username}' with role '{payload.role}'", 
        "SUCCESS"
    )

    return {"message": f"User '{payload.username}' created successfully in database", "user": new_u}

@router.get("/admin/audit-logs", dependencies=[Depends(require_roles(["SYSTEM_ADMIN"]))])
def get_audit_logs(limit: int = 100):
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        parsed_logs = []
        for line in reversed(lines[-limit:]):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                parsed_logs.append({
                    "timestamp": parts[0],
                    "user": parts[1].replace("User:", "").strip(),
                    "role": parts[2].replace("Role:", "").strip(),
                    "action": parts[3].replace("Action:", "").strip(),
                    "status": parts[4].replace("Status:", "").strip() if len(parts) > 4 else "SUCCESS",
                    "details": parts[5].replace("Details:", "").strip() if len(parts) > 5 else ""
                })
        return parsed_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read audit logs: {e}")

@router.get("/admin/system-stats", dependencies=[Depends(require_roles(["SYSTEM_ADMIN"]))])
def get_system_stats():
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    spatial_dir = os.path.join(ROOT, "data", "spatial")
    processed_dir = os.path.join(ROOT, "data", "processed")

    spatial_files = len(os.listdir(spatial_dir)) if os.path.exists(spatial_dir) else 0
    processed_files = len(os.listdir(processed_dir)) if os.path.exists(processed_dir) else 0
    users_count = len(list_all_users())

    return {
        "status": "HEALTHY",
        "version": "2.0.0-RBAC",
        "region": "Mumbai BMC (24 Wards)",
        "total_registered_users": users_count,
        "roles_active": list(PERMISSIONS.keys()),
        "spatial_layers_cataloged": spatial_files,
        "processed_datasets_cataloged": processed_files,
        "database_backend": "SQLite (data/urbansim_users.db)",
        "ml_models": [
            {"name": "Autoencoder Anomaly Detector", "version": "v2.1", "status": "ONLINE", "input_features": 15},
            {"name": "Deep Spatial Clustering", "version": "v1.4", "status": "ONLINE", "clusters": 4},
            {"name": "GraphSAGE / Urban GNN", "version": "v1.0", "status": "ONLINE", "nodes": 24},
            {"name": "Fixed-Reference Scenario Engine", "version": "v2.0", "status": "ONLINE", "scenarios": 5}
        ]
    }
