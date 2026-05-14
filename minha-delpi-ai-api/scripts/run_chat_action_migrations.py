from __future__ import annotations

from app.create_app import create_app
from app.extensions.db import db


MIGRATIONS = [
    """
    create extension if not exists pgcrypto;
    """,
    """
    create table if not exists ai_chat_agent_action_providers (
        id uuid primary key default gen_random_uuid(),
        agent_id uuid not null references ai_chat_agents(id) on delete cascade,
        provider_key varchar(120) not null,
        enabled boolean not null default true,
        allow_read boolean not null default true,
        allow_write boolean not null default false,
        allow_admin boolean not null default false,
        requires_confirmation_for_write boolean not null default true,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        constraint uq_ai_chat_agent_action_providers_agent_provider
            unique (agent_id, provider_key)
    );
    """,
    """
    create index if not exists ix_ai_chat_agent_action_providers_agent_id
        on ai_chat_agent_action_providers (agent_id);
    """,
    """
    create index if not exists ix_ai_chat_agent_action_providers_provider_key
        on ai_chat_agent_action_providers (provider_key);
    """,
    """
    create index if not exists ix_ai_chat_agent_action_providers_enabled
        on ai_chat_agent_action_providers (enabled);
    """,
    """
    create table if not exists ai_chat_agent_actions (
        id uuid primary key default gen_random_uuid(),
        agent_id uuid not null references ai_chat_agents(id) on delete cascade,
        provider_key varchar(120) not null,
        action_id varchar(300) not null,
        enabled boolean not null default true,
        sensitivity varchar(40) not null default 'read',
        requires_confirmation boolean not null default false,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now()
    );
    """,
    """
    create index if not exists ix_ai_chat_agent_actions_agent_id
        on ai_chat_agent_actions (agent_id);
    """,
    """
    create index if not exists ix_ai_chat_agent_actions_enabled
        on ai_chat_agent_actions (enabled);
    """,
    """
    create index if not exists ix_ai_chat_agent_actions_provider_key
        on ai_chat_agent_actions (provider_key);
    """,
    """
    create index if not exists ix_ai_chat_agent_actions_action_id
        on ai_chat_agent_actions (action_id);
    """,
]


CHECK_TABLES = [
    "ai_external_action_providers",
    "ai_external_action_schemas",
    "ai_external_actions",
    "ai_chat_agent_action_providers",
    "ai_chat_agent_actions",
]


def main() -> None:
    app = create_app()

    with app.app_context():
        print("Antes:")
        for table in CHECK_TABLES:
            exists = db.session.execute(
                db.text("select to_regclass(:table_name)"),
                {"table_name": f"public.{table}"},
            ).scalar()
            print(f"{table} => {exists}")

        for index, statement in enumerate(MIGRATIONS, start=1):
            print(f"Aplicando migration SQL {index}/{len(MIGRATIONS)}...")
            db.session.execute(db.text(statement))

        db.session.commit()

        print("\\nDepois:")
        for table in CHECK_TABLES:
            exists = db.session.execute(
                db.text("select to_regclass(:table_name)"),
                {"table_name": f"public.{table}"},
            ).scalar()
            print(f"{table} => {exists}")

        print("\\nOK: migrations de chat/actions aplicadas.")


if __name__ == "__main__":
    main()
