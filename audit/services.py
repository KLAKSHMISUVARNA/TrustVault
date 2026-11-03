import hashlib
import hmac
import json

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import AuditEvent


GENESIS_HASH = "0" * 64


def calculate_event_hash(payload):
    """
    Generate an HMAC-SHA256 hash from canonical event data.
    """
    secret = settings.AUDIT_HMAC_KEY.encode("utf-8")

    canonical_data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    return hmac.new(
        secret,
        canonical_data,
        hashlib.sha256
    ).hexdigest()


@transaction.atomic
def record_event(actor, action, target_type, target_id="", metadata=None):
    """
    Record an audit event linked to the previous event.
    """

    last_event = (
        AuditEvent.objects
        .select_for_update()
        .order_by("-id")
        .first()
    )

    previous_hash = (
        last_event.event_hash if last_event else GENESIS_HASH
    )

    timestamp = timezone.now()

    payload = {
        "actor_id": actor.pk if actor else None,
        "action": action,
        "target_type": target_type,
        "target_id": str(target_id),
        "metadata": metadata or {},
        "timestamp": timestamp.isoformat(),
        "previous_hash": previous_hash,
    }

    event_hash = calculate_event_hash(payload)

    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata=metadata or {},
        timestamp=timestamp,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )


def verify_audit_chain():
    """
    Verify event hashes and links throughout the audit chain.
    """

    expected_previous_hash = GENESIS_HASH

    for event in AuditEvent.objects.order_by("id"):

        payload = {
            "actor_id": event.actor_id,
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "metadata": event.metadata,
            "timestamp": event.timestamp.isoformat(),
            "previous_hash": event.previous_hash,
        }

        expected_hash = calculate_event_hash(payload)

        if event.previous_hash != expected_previous_hash:
            return False

        if not hmac.compare_digest(event.event_hash, expected_hash):
            return False

        expected_previous_hash = event.event_hash

    return True