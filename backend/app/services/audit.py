from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    resource: str,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            resource=resource,
            resource_id=resource_id,
            metadata_json=metadata,
        )
    )
    db.commit()

