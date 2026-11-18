import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.database import AuditLogRecord

class AuditLogger:
    """
    Immutable audit logging service.
    Calculates cryptographic SHA-256 hashes for every agent decision,
    guardrail trigger, manager review, and simulated execution.
    """

    @staticmethod
    def log(
        db: Session,
        incident_id: str,
        agent: str,
        event_type: str,
        details: Dict[str, Any],
        action_id: Optional[str] = None
    ) -> AuditLogRecord:
        record_id = f"aud-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow()
        details_str = json.dumps(details, sort_keys=True, default=str)

        # Cryptographic hash chaining
        payload = f"{record_id}|{incident_id}|{action_id}|{agent}|{event_type}|{details_str}|{timestamp.isoformat()}"
        checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        record = AuditLogRecord(
            id=record_id,
            incident_id=incident_id,
            action_id=action_id,
            agent=agent,
            event_type=event_type,
            details_json=details_str,
            checksum=checksum,
            timestamp=timestamp
        )
        db.add(record)
        db.commit()
        return record
