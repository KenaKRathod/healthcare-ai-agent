from datetime import datetime
from sqlalchemy.orm import Session
from backend.models import AuditLog


def log_audit_event(
    db: Session,
    username: str,
    role: str,
    action: str,
    resource: str,
    status: str = "SUCCESS"
):
    """
    Logs an access or alteration event to the audit_logs table for compliance tracking.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = AuditLog(
            timestamp=timestamp,
            username=username,
            role=role,
            action=action,
            resource=resource,
            status=status
        )
        db.add(log)
        db.commit()
    except Exception as e:
        # In a real environment, we would log this to syslogs or alert administrators.
        print(f"Failed to record audit log: {e}")
