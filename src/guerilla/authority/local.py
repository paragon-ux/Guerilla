"""Fixed local authorization profile for the Gate B workspace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from guerilla.authority.errors import AuthorityError

LOCAL_OWNER_PROFILE = "local-owner-v1"
LOCAL_OWNER_OPERATIONS = frozenset(
    {
        "graph.read",
        "graph.append",
        "adapter.observe",
        "adapter.act",
        "conflict.decide",
        "snapshot.read",
        "payload.read",
        "admin.configure",
    }
)


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    principal_id: str
    operation: str
    profile: str
    reason: str


@dataclass(frozen=True, slots=True)
class LocalAuthorizationProfile:
    owner_principal_id: str = "local-user"
    profile: str = LOCAL_OWNER_PROFILE

    def authorize(self, principal_id: str, operation: str) -> AuthorizationDecision:
        if self.profile != LOCAL_OWNER_PROFILE:
            return AuthorizationDecision(
                False,
                principal_id,
                operation,
                self.profile,
                "unsupported authorization profile",
            )
        if operation not in LOCAL_OWNER_OPERATIONS:
            return AuthorizationDecision(
                False,
                principal_id,
                operation,
                self.profile,
                "unsupported operation",
            )
        if principal_id != self.owner_principal_id:
            return AuthorizationDecision(
                False,
                principal_id,
                operation,
                self.profile,
                "principal is not workspace owner",
            )
        return AuthorizationDecision(True, principal_id, operation, self.profile, "allowed")

    def require(self, principal_id: str, operation: str) -> AuthorizationDecision:
        decision = self.authorize(principal_id, operation)
        if not decision.allowed:
            raise AuthorityError("unauthorized", decision.reason)
        return decision


def validate_authority_envelope(
    envelope: dict[str, Any],
    *,
    effective_principal_id: str,
    expected_profile: str = LOCAL_OWNER_PROFILE,
) -> None:
    if envelope.get("profile") != expected_profile:
        raise AuthorityError("authority_escalation", "authority profile cannot expand access")
    if envelope.get("authority_type") != "guerilla":
        raise AuthorityError("authority_escalation", "external authority cannot grant graph access")
    if envelope.get("principal_id") != effective_principal_id:
        raise AuthorityError("authority_escalation", "record authority principal is not effective")


def validate_member_authority(
    members: list[dict[str, Any]], *, effective_principal_id: str
) -> None:
    for member in members:
        authority = member.get("authority")
        if isinstance(authority, dict):
            validate_authority_envelope(
                authority,
                effective_principal_id=effective_principal_id,
            )
