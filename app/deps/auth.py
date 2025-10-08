from fastapi import Request, HTTPException, status
from firebase_admin import auth as admin_auth

def verify_firebase_token(request: Request, require_admin: bool = False):
    """
    Verify Firebase token and optionally check for admin claim.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing auth token"
        )
    
    token = auth_header.split(" ", 1)[1]
    try:
        decoded = admin_auth.verify_id_token(token)
        
        # Check admin claim if required
        if require_admin:
            if not decoded.get("isAdmin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
                
        return decoded
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid auth token"
        )