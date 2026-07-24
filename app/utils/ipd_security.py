# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# security = HTTPBearer()

# async def get_current_pharmacist(
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):

#     token_data = {"id": 1, "role": "pharmacist", "name": "John Doe"}
#     if token_data["role"] != "pharmacist":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized as pharmacist"
#         )
#     return token_data

from fastapi import Depends, HTTPException, status
from app.models.auth import User
from app.core.security import get_current_user


async def get_current_pharmacist(
    current_user: User = Depends(get_current_user),
) -> User:

    if current_user.role.lower() != "pharmacist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as pharmacist",
        )

    return current_user