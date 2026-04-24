"""Tests for security hardening: PII encryption, consent gating, tenant isolation, config validation."""

import pytest
from httpx import AsyncClient

from app.core.encryption import decrypt_pii, encrypt_pii


class TestPIIEncryption:
    """Tests for AES-256-GCM PII encryption at rest."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data should decrypt back to original."""
        original = "the wellness practitioner"
        encrypted = encrypt_pii(original)
        decrypted = decrypt_pii(encrypted)
        assert decrypted == original

    def test_encrypt_none_returns_none(self):
        """None input should return None."""
        assert encrypt_pii(None) is None
        assert decrypt_pii(None) is None

    def test_different_ciphertext_each_time(self):
        """Same plaintext should produce different ciphertext (nonce-based)."""
        enc1 = encrypt_pii("test")
        enc2 = encrypt_pii("test")
        assert enc1 != enc2

    def test_encrypted_value_is_not_plaintext(self):
        """Encrypted value should not contain the original text."""
        original = "123 Main Street, Anytown USA"
        encrypted = encrypt_pii(original)
        assert original not in encrypted

    def test_unicode_support(self):
        """Should handle unicode characters."""
        original = "Maria Garcia-Lopez"
        assert decrypt_pii(encrypt_pii(original)) == original

    def test_empty_string(self):
        """Empty string should encrypt and decrypt correctly."""
        assert decrypt_pii(encrypt_pii("")) == ""


class TestPIIConsentGating:
    """Tests for PII consent-based access control."""

    @pytest.mark.asyncio
    async def test_create_client_without_consent_rejects_pii(
        self, client: AsyncClient
    ):
        """Creating a client with PII but no consent should be rejected."""
        response = await client.post(
            "/api/v1/clients",
            json={
                "display_name": "Anonymous",
                "full_name": "Real Name",
                "pii_consent": False,
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_client_with_consent_accepts_pii(
        self, client: AsyncClient
    ):
        """Creating a client with PII and consent should succeed."""
        response = await client.post(
            "/api/v1/clients",
            json={
                "display_name": "Named Client",
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "pii_consent": True,
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["full_name"] == "Jane Doe"
        assert data["email"] == "jane@example.com"

    @pytest.mark.asyncio
    async def test_response_strips_pii_without_consent(
        self, client: AsyncClient
    ):
        """Client responses should not contain PII when consent is false."""
        response = await client.post(
            "/api/v1/clients",
            json={"display_name": "No PII Client", "pii_consent": False},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["full_name"] is None
        assert data["email"] is None
        assert data["phone"] is None
        assert data["address"] is None
        assert data["display_name"] == "No PII Client"

    @pytest.mark.asyncio
    async def test_create_client_without_consent_allows_no_pii(
        self, client: AsyncClient
    ):
        """Creating a client without consent and without PII should succeed."""
        response = await client.post(
            "/api/v1/clients",
            json={"display_name": "Anonymous Client"},
        )
        assert response.status_code == 201


class TestTenantIsolation:
    """Tests for multi-tenancy data isolation."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_client(
        self, client: AsyncClient, db_session
    ):
        """User should not be able to access another user's client."""
        import uuid
        from app.core.security import hash_password
        from app.db.models.client import Client
        from app.db.models.user import User

        # Create another user and their client directly in DB
        other_user = User(
            id=uuid.uuid4(),
            email="other@example.com",
            password_hash=hash_password("otherpassword1"),
            full_name="Other User",
            role="practitioner",
        )
        db_session.add(other_user)
        await db_session.flush()

        other_client = Client(
            user_id=other_user.id,
            display_name="Other's Client",
        )
        db_session.add(other_client)
        await db_session.commit()

        # Try to access the other user's client
        response = await client.get(f"/api/v1/clients/{other_client.id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_only_own_clients(self, client: AsyncClient, db_session):
        """List should only return the authenticated user's clients."""
        import uuid
        from app.core.security import hash_password
        from app.db.models.client import Client
        from app.db.models.user import User

        # Create another user with a client
        other_user = User(
            id=uuid.uuid4(),
            email="other2@example.com",
            password_hash=hash_password("otherpassword1"),
            full_name="Other User 2",
            role="practitioner",
        )
        db_session.add(other_user)
        await db_session.flush()

        other_client = Client(
            user_id=other_user.id,
            display_name="Should Not See This",
        )
        db_session.add(other_client)
        await db_session.commit()

        # Create our own client
        await client.post(
            "/api/v1/clients",
            json={"display_name": "My Client"},
        )

        # List should only show our client
        response = await client.get("/api/v1/clients")
        clients_list = response.json()["data"]
        names = [c["display_name"] for c in clients_list]
        assert "My Client" in names
        assert "Should Not See This" not in names


class TestProductionConfigValidation:
    """Tests for production secret validation."""

    def test_default_jwt_secret_flagged(self):
        """Default JWT secret should fail validation."""
        from app.core.config import Settings

        s = Settings(
            environment="production",
            jwt_secret="CHANGE-ME-IN-PRODUCTION",
            pii_encryption_key="Xflo5X8fyKteHOxq5i6hwWYqGLdWNbJsg0UchY8Nsbc=",
        )
        errors = s.validate_production_secrets()
        assert any("JWT_SECRET" in e for e in errors)

    def test_missing_pii_key_flagged(self):
        """Missing PII encryption key should fail validation."""
        from app.core.config import Settings

        s = Settings(
            environment="production",
            jwt_secret="a-real-secret-value",
            pii_encryption_key="",
        )
        errors = s.validate_production_secrets()
        assert any("PII_ENCRYPTION_KEY" in e for e in errors)

    def test_valid_production_config_passes(self):
        """Properly configured production settings should pass."""
        from app.core.config import Settings

        s = Settings(
            environment="production",
            jwt_secret="a-strong-random-secret-value-here",
            pii_encryption_key="Xflo5X8fyKteHOxq5i6hwWYqGLdWNbJsg0UchY8Nsbc=",
            database_ssl=True,
            debug=False,
            database_url="postgresql+asyncpg://user:pass@prod-host:5432/db",
        )
        errors = s.validate_production_secrets()
        assert len(errors) == 0


class TestClientExportAndPurge:
    """Tests for data export and hard-delete."""

    @pytest.mark.asyncio
    async def test_export_client_data(self, client: AsyncClient):
        """Export should return all client data including sessions."""
        # Create client
        c_resp = await client.post(
            "/api/v1/clients",
            json={"display_name": "Export Test"},
        )
        client_id = c_resp.json()["data"]["id"]

        # Create a session
        await client.post(
            "/api/v1/audits",
            json={"client_id": client_id},
        )

        # Export
        export_resp = await client.post(f"/api/v1/clients/{client_id}/export")
        assert export_resp.status_code == 200
        data = export_resp.json()["data"]
        assert data["client"]["display_name"] == "Export Test"
        assert len(data["sessions"]) == 1
        assert "exported_at" in data

    @pytest.mark.asyncio
    async def test_purge_client(self, client: AsyncClient):
        """Purge should permanently delete client and all related data."""
        # Create client with session and observation
        c_resp = await client.post(
            "/api/v1/clients",
            json={"display_name": "Purge Test"},
        )
        client_id = c_resp.json()["data"]["id"]

        s_resp = await client.post(
            "/api/v1/audits",
            json={"client_id": client_id},
        )
        session_id = s_resp.json()["data"]["id"]

        await client.post(
            f"/api/v1/audits/{session_id}/observations",
            json={"room_area": "entry", "content": "Test observation"},
        )

        # Purge
        purge_resp = await client.delete(f"/api/v1/clients/{client_id}/purge")
        assert purge_resp.status_code == 200

        # Client should be gone (not just soft-deleted)
        get_resp = await client.get(f"/api/v1/clients/{client_id}")
        assert get_resp.status_code == 404
