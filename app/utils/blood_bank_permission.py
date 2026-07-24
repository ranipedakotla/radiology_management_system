from fastapi import Depends, HTTPException, status
from typing import List
from app.models.auth import User
from app.models.blood_bank import UserRole
from app.core.security import get_current_user


def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to perform this action"
            )
        return current_user

    return role_checker
