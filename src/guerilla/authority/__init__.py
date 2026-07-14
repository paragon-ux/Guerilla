"""Local authorization and authority-bound registry helpers."""

from guerilla.authority.errors import AuthorityError, BoundaryError, IdentityConflictError
from guerilla.authority.local import (
    LOCAL_OWNER_OPERATIONS,
    LOCAL_OWNER_PROFILE,
    AuthorizationDecision,
    LocalAuthorizationProfile,
    validate_authority_envelope,
    validate_member_authority,
)
from guerilla.authority.registries import (
    REGISTRY_METADATA_KEY,
    AdapterIdentityRegistry,
    BoundaryRegistry,
    ExternalIdentityRegistry,
    ExternalSystemRegistration,
)

__all__ = [
    "AuthorizationDecision",
    "AuthorityError",
    "BoundaryError",
    "IdentityConflictError",
    "LOCAL_OWNER_OPERATIONS",
    "LOCAL_OWNER_PROFILE",
    "REGISTRY_METADATA_KEY",
    "AdapterIdentityRegistry",
    "BoundaryRegistry",
    "ExternalIdentityRegistry",
    "ExternalSystemRegistration",
    "LocalAuthorizationProfile",
    "validate_authority_envelope",
    "validate_member_authority",
]
