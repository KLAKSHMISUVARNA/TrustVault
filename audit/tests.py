from django.test import TestCase

from .models import AuditEvent
from .services import record_event, verify_audit_chain


class AuditIntegrityTests(TestCase):

    def test_single_event_creates_valid_chain(self):
        record_event(
            actor=None,
            action="DOCUMENT_VIEWED",
            target_type="DOCUMENT",
            target_id="1",
            metadata={"result": "success"}
        )

        self.assertEqual(AuditEvent.objects.count(), 1)
        self.assertTrue(verify_audit_chain())

    def test_multiple_events_create_valid_chain(self):
        record_event(
            actor=None,
            action="DOCUMENT_VIEWED",
            target_type="DOCUMENT",
            target_id="1"
        )

        record_event(
            actor=None,
            action="PERMISSION_GRANTED",
            target_type="DOCUMENT",
            target_id="1"
        )

        self.assertEqual(AuditEvent.objects.count(), 2)
        self.assertTrue(verify_audit_chain())

    def test_metadata_tampering_is_detected(self):
        event = record_event(
            actor=None,
            action="DOCUMENT_VIEWED",
            target_type="DOCUMENT",
            target_id="1",
            metadata={"status": "success"}
        )

        event.metadata = {"status": "tampered"}
        event.save(update_fields=["metadata"])

        self.assertFalse(verify_audit_chain())

    def test_previous_hash_tampering_is_detected(self):
        first = record_event(
            actor=None,
            action="DOCUMENT_VIEWED",
            target_type="DOCUMENT",
            target_id="1"
        )

        record_event(
            actor=None,
            action="PERMISSION_GRANTED",
            target_type="DOCUMENT",
            target_id="1"
        )

        first.previous_hash = "f" * 64
        first.save(update_fields=["previous_hash"])

        self.assertFalse(verify_audit_chain())