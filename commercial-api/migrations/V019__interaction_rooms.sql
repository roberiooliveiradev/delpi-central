-- Interaction rooms (entity / process / wall). Do not edit V004; extend owner_type here.
-- Spec: docs/12-roadmap-e-evolucao/commercial/DATA-MODEL.md § 8.1

CREATE TABLE IF NOT EXISTS commercial.interaction_rooms (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind                  TEXT NOT NULL,
    entity_type           TEXT,
    entity_key            TEXT,
    group_id              UUID
        REFERENCES commercial.commercial_groups (id) ON DELETE SET NULL,
    title                 TEXT NOT NULL,
    created_by_user_id    TEXT NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at            TIMESTAMPTZ,
    CONSTRAINT interaction_rooms_kind_ck CHECK (
        kind IN ('entity', 'process', 'wall')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_commercial_interaction_rooms_entity
    ON commercial.interaction_rooms (kind, entity_type, entity_key)
    WHERE kind = 'entity' AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_commercial_interaction_rooms_wall_group
    ON commercial.interaction_rooms (kind, group_id)
    WHERE kind = 'wall' AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_rooms_updated
    ON commercial.interaction_rooms (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_rooms_entity
    ON commercial.interaction_rooms (kind, entity_type, entity_key);

CREATE TABLE IF NOT EXISTS commercial.interaction_room_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id         UUID NOT NULL
        REFERENCES commercial.interaction_rooms (id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'member',
    last_read_at    TIMESTAMPTZ,
    muted           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT interaction_room_members_role_ck CHECK (
        role IN ('member', 'watcher')
    ),
    UNIQUE (room_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_room_members_user
    ON commercial.interaction_room_members (user_id);

CREATE TABLE IF NOT EXISTS commercial.interaction_messages (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id           UUID NOT NULL
        REFERENCES commercial.interaction_rooms (id) ON DELETE CASCADE,
    parent_id         UUID
        REFERENCES commercial.interaction_messages (id) ON DELETE SET NULL,
    author_user_id    TEXT,
    message_kind      TEXT NOT NULL,
    body_text         TEXT NOT NULL DEFAULT '',
    edited_at         TIMESTAMPTZ,
    deleted_at        TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT interaction_messages_kind_ck CHECK (
        message_kind IN ('text', 'system', 'task_ref', 'pin')
    )
);

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_messages_room_created
    ON commercial.interaction_messages (room_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_messages_parent
    ON commercial.interaction_messages (parent_id)
    WHERE parent_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS commercial.interaction_mentions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id     UUID NOT NULL
        REFERENCES commercial.interaction_messages (id) ON DELETE CASCADE,
    mention_kind   TEXT NOT NULL,
    ref            JSONB NOT NULL,
    label          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_mentions_kind
    ON commercial.interaction_mentions (mention_kind);

CREATE INDEX IF NOT EXISTS idx_commercial_interaction_mentions_ref
    ON commercial.interaction_mentions USING GIN (ref);

CREATE TABLE IF NOT EXISTS commercial.interaction_reactions (
    message_id    UUID NOT NULL
        REFERENCES commercial.interaction_messages (id) ON DELETE CASCADE,
    user_id       TEXT NOT NULL,
    code          TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (message_id, user_id, code)
);

CREATE TABLE IF NOT EXISTS commercial.interaction_pins (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id              UUID NOT NULL
        REFERENCES commercial.interaction_rooms (id) ON DELETE CASCADE,
    message_id           UUID NOT NULL
        REFERENCES commercial.interaction_messages (id) ON DELETE CASCADE,
    pinned_by_user_id    TEXT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (room_id, message_id)
);

ALTER TABLE commercial.attachments
    DROP CONSTRAINT IF EXISTS attachments_owner_type_check;

ALTER TABLE commercial.attachments
    ADD CONSTRAINT attachments_owner_type_check
    CHECK (owner_type IN ('task', 'customer', 'activity', 'room_message'));
