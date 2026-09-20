import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# Secret key for JWT signing
SECRET_KEY = os.getenv("URBANSIM_JWT_SECRET", "urbansim_civic_ai_super_secret_jwt_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Audit Log Path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_LOG_FILE = os.path.join(ROOT_DIR, "logs", "audit.log")
os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)

# --------------------------------------------------
# PASSWORD HASHING
# --------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# --------------------------------------------------
# DEVELOPMENT SEED USERS & ROLES
# --------------------------------------------------
USERS_DB: Dict[str, Dict[str, Any]] = {
    "citizen": {
        "username": "citizen",
        "email": "citizen@urbansim.local",
        "name": "Aarav Sharma",
        "password": hash_password("citizen123"),
        "role": "CITIZEN",
        "ward": "GS",
        "is_active": True
    },
    "analyst": {
        "username": "analyst",
        "email": "analyst@urbansim.local",
        "name": "Dr. Ananya Desai",
        "password": hash_password("analyst123"),
        "role": "URBAN_ANALYST",
        "ward": "All",
        "is_active": True
    },
    "authority": {
        "username": "authority",
        "email": "authority@urbansim.local",
        "name": "Rajesh Kulkarni (BMC Assistant Commissioner)",
        "password": hash_password("authority123"),
        "role": "URBAN_AUTHORITY",
        "ward": "All",
        "is_active": True
    },
    "admin": {
        "username": "admin",
        "email": "admin@urbansim.local",
        "name": "System Administrator",
        "password": hash_password("admin123"),
        "role": "SYSTEM_ADMIN",
        "ward": "All",
        "is_active": True
    }
}

# --------------------------------------------------
# PERMISSION MATRIX
# --------------------------------------------------
PERMISSIONS: Dict[str, List[str]] = {
    "CITIZEN": [
        "public_gis:view",
        "ward_info:view",
        "facilities:view",
        "complaints:submit",
        "complaints:view_own",
        "environment_public:view"
    ],
    "URBAN_ANALYST": [
        "public_gis:view",
        "ward_info:view",
        "facilities:view",
        "all_lenses:view",
        "ai_models:view",
        "anomalies:view",
        "scenarios:simulate",
        "comparison:execute",
        "methodology:view",
        "evidence:inspect"
    ],
    "URBAN_AUTHORITY": [
        "public_gis:view",
        "ward_info:view",
        "facilities:view",
        "operational_dashboard:view",
        "complaints:manage_all",
        "infrastructure_pressure:monitor",
        "environment:monitor",
        "scenarios:evaluate",
        "comparison:execute"
    ],
    "SYSTEM_ADMIN": [
        "public_gis:view",
        "ward_info:view",
        "facilities:view",
        "all_lenses:view",
        "ai_models:view",
        "anomalies:view",
        "scenarios:simulate",
        "comparison:execute",
        "operational_dashboard:view",
        "complaints:manage_all",
        "users:manage",
        "roles:manage",
        "data_sources:manage",
        "gis_layers:manage",
        "models:manage",
        "audit_logs:view",
        "system:admin"
    ]
}

# --------------------------------------------------
# AUDIT LOGGING
# --------------------------------------------------
def log_audit_event(username: str, role: str, action: str, status: str = "SUCCESS", details: str = ""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | User: {username} | Role: {role} | Action: {action} | Status: {status} | Details: {details}\n"
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Error writing audit log: {e}")

# --------------------------------------------------
# JWT TOKENS
# --------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

from app.db.database import get_user_by_username_or_email, list_all_users

# --------------------------------------------------
# FASTAPI SECURITY DEPENDENCIES
# --------------------------------------------------
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or session revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 1. Lookup in SQLite database
    user = get_user_by_username_or_email(username)
    
    # 2. Fallback to in-memory dictionary if needed
    if not user and username in USERS_DB:
        user = USERS_DB[username]
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or session revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.get("is_active", 1):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
        
    return {
        "username": user["username"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "ward": user.get("ward", "All"),
        "permissions": PERMISSIONS.get(user["role"], [])
    }

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles and user_role != "SYSTEM_ADMIN":
            log_audit_event(
                current_user["username"], 
                user_role, 
                f"Unauthorized route access attempt (Required: {allowed_roles})", 
                "DENIED"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_permission(permission: str):
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_perms = current_user.get("permissions", [])
        if permission not in user_perms and current_user.get("role") != "SYSTEM_ADMIN":
            log_audit_event(
                current_user["username"], 
                current_user["role"], 
                f"Unauthorized permission attempt (Required: {permission})", 
                "DENIED"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing permission: {permission}"
            )
        return current_user
    return permission_checker
