import json
import hashlib
import hmac
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.database import AuditLogRecord
from backend.app.config import settings

class AuditLogger:
    """
    Immutable audit logging service with chained cryptographic SHA-256 provenance.
    Every record links to the checksum of the previous entry, establishing a tamper-evident log.
    """

    @classmethod
    def get_latest_checksum(cls, db: Session) -> str:
        """Fetch the most recent audit checksum or the genesis seed."""
        last_record = db.query(AuditLogRecord).order_by(AuditLogRecord.timestamp.desc(), AuditLogRecord.id.desc()).first()
        if last_record and last_record.checksum:
            return last_record.checksum
        return settings.audit_genesis_hash

    @classmethod
    def compute_hash(
        cls,
        record_id: str,
        incident_id: str,
        action_id: Optional[str],
        agent: str,
        event_type: str,
        details_str: str,
        timestamp_iso: str,
        previous_checksum: str
    ) -> str:
        """Deterministically compute SHA-256 chained checksum."""
        payload = (
            f"{record_id}|{incident_id}|{action_id or ''}|{agent}|"
            f"{event_type}|{details_str}|{timestamp_iso}|{previous_checksum}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def log(
        cls,
        db: Session,
        incident_id: str,
        agent: str,
        event_type: str,
        details: Dict[str, Any],
        action_id: Optional[str] = None
    ) -> AuditLogRecord:
        record_id = f"aud-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow()
        timestamp_iso = timestamp.isoformat()
        details_str = json.dumps(details, sort_keys=True, default=str)

        # Retrieve prior block hash
        prev_hash = cls.get_latest_checksum(db)

        # Compute tamper-evident chained hash
        checksum = cls.compute_hash(
            record_id=record_id,
            incident_id=incident_id,
            action_id=action_id,
            agent=agent,
            event_type=event_type,
            details_str=details_str,
            timestamp_iso=timestamp_iso,
            previous_checksum=prev_hash
        )

        record = AuditLogRecord(
            id=record_id,
            incident_id=incident_id,
            action_id=action_id,
            agent=agent,
            event_type=event_type,
            details_json=details_str,
            previous_checksum=prev_hash,
            checksum=checksum,
            timestamp=timestamp
        )
        db.add(record)
        db.commit()
        return record

    @classmethod
    def verify_chain_integrity(cls, db: Session) -> Tuple[bool, Optional[str], int]:
        """
        Validates the entire audit log chain using constant-time hash verification.
        Returns (is_valid: bool, error_message: Optional[str], total_verified: int).
        """
        records = db.query(AuditLogRecord).order_by(AuditLogRecord.timestamp.asc(), AuditLogRecord.id.asc()).all()
        if not records:
            return True, None, 0

        expected_prev = settings.audit_genesis_hash

        for idx, rec in enumerate(records):
            # 1. Verify previous checksum matches
            if rec.previous_checksum and not hmac.compare_digest(rec.previous_checksum, expected_prev):
                return False, f"Broken chain link at index {idx} ({rec.id}): expected previous {expected_prev}, got {rec.previous_checksum}", idx

            # 2. Recalculate checksum
            timestamp_iso = rec.timestamp.isoformat() if rec.timestamp else ""
            recomputed = cls.compute_hash(
                record_id=rec.id,
                incident_id=rec.incident_id,
                action_id=rec.action_id,
                agent=rec.agent,
                event_type=rec.event_type,
                details_str=rec.details_json,
                timestamp_iso=timestamp_iso,
                previous_checksum=rec.previous_checksum or expected_prev
            )

            if not hmac.compare_digest(recomputed, rec.checksum):
                return False, f"Tampered record at {rec.id}: expected hash {recomputed}, recorded {rec.checksum}", idx

            expected_prev = rec.checksum

        return True, None, len(records)
