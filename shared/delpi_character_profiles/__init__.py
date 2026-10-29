"""Shared DELPI character-profile contract (SHARED-CHARACTER-PROFILES-001).

``shared`` owns the *structure* — models, validation, serialization,
projections, versioning. Each MCP/app owns its own *character*: fills a
local ``CharacterProfile``, versions it, and decides how to project it into
its interface (instructions, directives, resources).

Deliberately NOT here (per the spec):

- pre-filled profiles (DAVI, VISTA, …) — fichas live in each MCP;
- a central character registry, discovery service or MCP-to-MCP calls;
- auth, authorization, tool catalogs or any operational truth;
- SDK (mcp/openai), HTTP, DB or Keycloak dependencies.

Distribution of public projections is a TARGET owned by consumers and the
approved publication mechanism — this package only serializes/validates.
"""

from .models import (
    AVATAR_STATUSES,
    FICTION_IDENTITY_ONLY,
    PUBLIC_PROJECTION_VERSION,
    RELATIONSHIP_INVERSES,
    RELATIONSHIP_TYPES,
    RELATIONSHIP_VISIBILITY,
    SCHEMA_VERSION,
    Appearance,
    CharacterProfile,
    CharacterPublicProfile,
    CharacterRelationship,
    CharacterStory,
    CoexistenceRules,
    CommunicationStyle,
    Expertise,
    Identity,
    Personality,
    ProfessionalConduct,
    StoryEvent,
)
from .projection import (
    project_identity_summary,
    project_persona_context,
    project_public_profile,
)
from .serialization import (
    dumps_deterministic,
    profile_from_dict,
    profile_to_dict,
    profile_to_json,
    public_profile_from_dict,
    public_profile_to_dict,
    public_profile_to_json,
)
from .validation import (
    ValidationIssue,
    validate_profile,
    validate_public_profile,
    validate_relationship_consistency,
)
from .versioning import (
    CompatibilityCheck,
    CompatibilityStatus,
    IncompatibleVersionError,
    assert_public_projection_compatible,
    assert_schema_compatible,
    check_public_projection_compatibility,
    check_schema_compatibility,
)

__all__ = [
    "AVATAR_STATUSES",
    "Appearance",
    "CharacterProfile",
    "CharacterPublicProfile",
    "CharacterRelationship",
    "CharacterStory",
    "CoexistenceRules",
    "CommunicationStyle",
    "CompatibilityCheck",
    "CompatibilityStatus",
    "Expertise",
    "FICTION_IDENTITY_ONLY",
    "Identity",
    "IncompatibleVersionError",
    "PUBLIC_PROJECTION_VERSION",
    "Personality",
    "ProfessionalConduct",
    "RELATIONSHIP_INVERSES",
    "RELATIONSHIP_TYPES",
    "RELATIONSHIP_VISIBILITY",
    "SCHEMA_VERSION",
    "StoryEvent",
    "ValidationIssue",
    "assert_public_projection_compatible",
    "assert_schema_compatible",
    "check_public_projection_compatibility",
    "check_schema_compatibility",
    "dumps_deterministic",
    "profile_from_dict",
    "profile_to_dict",
    "profile_to_json",
    "project_identity_summary",
    "project_persona_context",
    "project_public_profile",
    "public_profile_from_dict",
    "public_profile_to_dict",
    "public_profile_to_json",
    "validate_profile",
    "validate_public_profile",
    "validate_relationship_consistency",
]
