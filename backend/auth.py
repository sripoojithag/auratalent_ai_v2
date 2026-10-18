import os
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

# Security bearer scheme
security = HTTPBearer(auto_error=False)

# Lazy Firebase Admin App initialization
_firebase_initialized = False


def init_firebase_admin():
    global _firebase_initialized
    if _firebase_initialized:
        return

    try:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.environ.get("FIREBASE_PROJECT_ID")

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
        elif project_id:
            firebase_admin.initialize_app(options={"projectId": project_id})
            _firebase_initialized = True
        else:
            firebase_admin.initialize_app()
            _firebase_initialized = True
    except Exception as e:
        # If already initialized or in test environment
        if "The default Firebase app already exists" in str(e):
            _firebase_initialized = True
        else:
            print(f"Warning: Firebase Admin initialization: {e}")


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """
    Validates Firebase Bearer token from Authorization header.
    Rejects missing or invalid tokens with HTTP 401.
    """
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.credentials
    init_firebase_admin()

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_optional_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    Permissive token validator for endpoints where auth is optional.
    """
    if not auth_header or not auth_header.credentials:
        return None

    try:
        init_firebase_admin()
        return firebase_auth.verify_id_token(auth_header.credentials)
    except Exception:
        return None
