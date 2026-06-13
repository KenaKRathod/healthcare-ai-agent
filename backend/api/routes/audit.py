from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.auth import check_role
from backend.models import AuditLog, User

router = APIRouter()


@router.get("/audit-logs")
def get_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(check_role(["doctor"]))],
    limit: int = 100,
    offset: int = 0,
):
    """
    Fetch system audit logs for security compliance verification. Restricted to Doctor role.
    """
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs
