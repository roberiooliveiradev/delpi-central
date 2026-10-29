"""Shared DELPI character-profile contract models.

Narrative identity contract for DELPI specialists (DAVI, VISTA, TÉO, EVA,
CLARA, ...). Shared owns the *structure*; each MCP/app owns and fills its
own local profile. These models carry fiction only: they never represent
tools, permissions, capabilities, authorization or service dependencies.

Design rules:

- ``dataclasses(frozen=True)`` + tuples: profiles are immutable values.
- All fields optional except identity keys — a profile can grow over time
  without schema churn.
- No SDK (mcp/openai), HTTP, DB or auth imports — pure stdlib contract.
- English identifiers; prose content may be pt-BR per the app content
  layer conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 1
PUBLIC_PROJECTION_VERSION = 1

# Narrative classification marker every profile must keep: fiction is never
# operational truth, authorization or integration.
FICTION_IDENTITY_ONLY = "FICTION_IDENTITY_ONLY"

# Approval states for visual identity / avatar references.
AVATAR_STATUSES = frozenset(
    {
        "UNSET",
        "REFERENCE_NOT_OFFICIAL_AVATAR",
        "OFFICIAL_AVATAR_APPROVED",
    }
)

# Approved relationship vocabulary. Extensible by convention: unknown types
# are reported as warnings (not hard failures) so new relation kinds do not
# require a contract release, provided they stay snake_case.
RELATIONSHIP_TYPES = frozenset(
    {
        "friendship",
        "colleagues",
        "mentorship",
        "mentee",
        "romantic_partner",
        "narrative_partnership",
        "friendly_rivalry",
        "family",
        "acquaintance",
        "other",
    }
)

# Relationship types that imply a reciprocal declaration on the target
# profile, and the expected inverse type. Used by
# ``validation.validate_relationship_consistency``; a missing target profile
# yields an unresolved-reference warning, never a hard failure — fichas are
# allowed to reference characters whose profile is not yet published.
RELATIONSHIP_INVERSES = {
    "romantic_partner": "romantic_partner",
    "friendship": "friendship",
    "colleagues": "colleagues",
    "narrative_partnership": "narrative_partnership",
    "friendly_rivalry": "friendly_rivalry",
    "mentorship": "mentee",
    "mentee": "mentorship",
}

# Who may see a relationship in the public projection.
RELATIONSHIP_VISIBILITY = frozenset({"public", "internal"})


@dataclass(frozen=True)
class Identity:
    """Stable identity keys plus optional narrative demographics.

    ``character_id`` is the durable cross-profile key (snake_case slug) —
    display names may change, the id must not. ``narrative_age`` and
    ``gender_identity`` accept absence: not every character defines them.
    """

    character_id: str
    name: str
    display_name: str = ""
    title: str = ""
    role: str = ""
    organization: str = ""
    narrative_age: str | None = None
    gender_identity: str | None = None
    pronouns: str | None = None
    short_introduction: str = ""


@dataclass(frozen=True)
class Appearance:
    """Physical/visual reference — narrative only.

    ``avatar_status`` distinguishes a mere narrative/visual reference from
    an officially approved avatar; ``REFERENCE_NOT_OFFICIAL_AVATAR`` is the
    default so nothing is promoted to official by accident. Serves §5.2 and
    §11 (visual identity) of the contract spec without duplicating fields.
    """

    age_appearance: str = ""
    height_description: str = ""
    build: str = ""
    skin: str = ""
    hair: str = ""
    eyes: str = ""
    face: str = ""
    glasses: str = ""
    clothing: str = ""
    accessories: str = ""
    distinctive_features: tuple[str, ...] = ()
    visual_style: str = ""
    color_palette: tuple[str, ...] = ()
    avatar_reference: str = ""
    avatar_status: str = "REFERENCE_NOT_OFFICIAL_AVATAR"


@dataclass(frozen=True)
class Personality:
    """Trait model — no single personality is imposed on any character."""

    core_traits: tuple[str, ...] = ()
    secondary_traits: tuple[str, ...] = ()
    temperament: str = ""
    humor_style: str = ""
    curiosity: str = ""
    energy: str = ""
    social_style: str = ""
    strengths: tuple[str, ...] = ()
    quirks: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommunicationStyle:
    """Voice model — each MCP keeps its own voice; nothing forces catch-phrase
    repetition on every response."""

    language: str = "pt-BR"
    tone: str = ""
    formality: str = ""
    verbosity: str = ""
    greeting_style: str = ""
    preferred_expressions: tuple[str, ...] = ()
    humor_frequency: str = ""
    explanation_style: str = ""
    clarification_style: str = ""


@dataclass(frozen=True)
class Expertise:
    """Narrative specialization and reasoning style.

    NOT a tool catalog, capability list or permission grant — operational
    authority stays with the owning backend.
    """

    specialties: tuple[str, ...] = ()
    knowledge_domains: tuple[str, ...] = ()
    professional_role: str = ""
    reasoning_style: str = ""
    problem_solving_style: str = ""


@dataclass(frozen=True)
class StoryEvent:
    """One narrative event. ``event_id`` is stable; ``narrative_date`` is
    optional and never an operational timestamp — fiction has its own clock."""

    event_id: str
    title: str
    description: str = ""
    narrative_date: str = ""
    participants: tuple[str, ...] = ()
    significance: str = ""
    status: str = "canonical"


@dataclass(frozen=True)
class CharacterStory:
    """Full narrative history: origin, trajectory, events, evolution.

    New events and arcs are added without schema changes; file history lives
    in Git, not inside the model.
    """

    origin_story: str = ""
    background: str = ""
    how_joined_organization: str = ""
    personal_mission: str = ""
    motivations: tuple[str, ...] = ()
    values: tuple[str, ...] = ()
    interests: tuple[str, ...] = ()
    habits: tuple[str, ...] = ()
    important_memories: tuple[str, ...] = ()
    current_story_arc: str = ""
    events: tuple[StoryEvent, ...] = ()


@dataclass(frozen=True)
class CharacterRelationship:
    """Edge from this character to ``target_character_id``.

    ``shared_story_event_ids`` may reference events not resolvable until the
    target profile exists — unresolved references are tolerated (warning).
    """

    target_character_id: str
    relationship_type: str
    description: str = ""
    narrative_status: str = "active"
    since: str = ""
    shared_story_event_ids: tuple[str, ...] = ()
    visibility: str = "public"


@dataclass(frozen=True)
class CoexistenceRules:
    """Narrative coexistence guidelines — how the character references
    colleagues without repetition, invention or false capability claims."""

    guidelines: tuple[str, ...] = ()
    mention_frequency: str = "occasional"
    allowed_reference_contexts: tuple[str, ...] = ()
    forbidden_behaviors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProfessionalConduct:
    """Conversational behavior. Narrative configuration only — nothing here
    authorizes an operation or overrides backend policy."""

    answer_first: bool = True
    clarification_preferences: str = ""
    proactive_suggestions: str = ""
    response_structure: str = ""
    error_communication: str = ""
    user_guidance: str = ""
    humor_boundaries: str = ""


@dataclass(frozen=True)
class CharacterProfile:
    """Root profile aggregate. Each MCP/app fills one locally; the shared
    package stores no pre-filled profiles."""

    identity: Identity
    profile_version: int = 1
    schema_version: int = SCHEMA_VERSION
    universe: str = "Especialistas DELPI"
    appearance: Appearance = field(default_factory=Appearance)
    personality: Personality = field(default_factory=Personality)
    communication: CommunicationStyle = field(default_factory=CommunicationStyle)
    expertise: Expertise = field(default_factory=Expertise)
    story: CharacterStory = field(default_factory=CharacterStory)
    relationships: tuple[CharacterRelationship, ...] = ()
    coexistence: CoexistenceRules = field(default_factory=CoexistenceRules)
    conduct: ProfessionalConduct = field(default_factory=ProfessionalConduct)
    narrative_classification: str = FICTION_IDENTITY_ONLY


@dataclass(frozen=True)
class CharacterPublicProfile:
    """Approved narrative summary exchanged between MCPs so specialists can
    know each other — eventual, narrative knowledge, never an operational
    dependency. Contains no credentials, permissions, operational data or
    infrastructure details."""

    character_id: str
    public_projection_version: int = PUBLIC_PROJECTION_VERSION
    display_name: str = ""
    role: str = ""
    short_introduction: str = ""
    personality_summary: str = ""
    appearance_summary: str = ""
    story_summary: str = ""
    relationships: tuple[CharacterRelationship, ...] = ()
    profile_version: int = 1
    universe: str = ""
