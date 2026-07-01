from fastapi import Header, HTTPException, status

from .config import settings


def require_admin(x_findy_admin_key: str = Header(default="")) -> None:
    if x_findy_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 인증이 필요합니다.",
        )

