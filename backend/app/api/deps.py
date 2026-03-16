from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db


def get_admin_actor(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> str:
    settings = get_settings()
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return "admin"


DBSession = Annotated[Session, Depends(get_db)]
AdminActor = Annotated[str, Depends(get_admin_actor)]

