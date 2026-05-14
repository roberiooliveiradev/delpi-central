from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.create_app import create_app
from app.extensions.db import db


@dataclass(frozen=True)
class Migration:
    key: str
    description: str
    sql: str


MIGRATIONS: list[Migration] = [
    Migration(
        "000_extensions_pgcrypto",
        "Garante extensão pgcrypto para gen_random_uuid",
        """
        create extension if not exists pgcrypto;
        """,
    ),

    Migration(
        "010_external_action_providers_table",
        "Cria tabela global de providers de actions",
        """
        create table if not exists ai_external_action_providers (
            id uuid primary key default gen_random_uuid(),
            provider_key varchar(80) not null unique,
            name varchar(150) not null,
            provider_type varchar(20) not null,
            base_url text not null,
            openapi_url text null,
            privacy_policy_url text null,
            auth_mode varchar(40) not null default 'none',
            auth_config jsonb null,
            enabled boolean not null default true,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        );
        """,
    ),

    Migration(
        "011_external_action_providers_columns",
        "Atualiza colunas de providers de actions",
        """
        alter table ai_external_action_providers
            add column if not exists openapi_url text null,
            add column if not exists privacy_policy_url text null,
            add column if not exists auth_mode varchar(40) not null default 'none',
            add column if not exists auth_config jsonb null,
            add column if not exists enabled boolean not null default true,
            add column if not exists created_at timestamptz not null default now(),
            add column if not exists updated_at timestamptz not null default now();
        """,
    ),

    Migration(
        "012_external_action_providers_indexes",
        "Cria índices de providers de actions",
        """
        create index if not exists ix_ai_external_action_providers_provider_key
            on ai_external_action_providers (provider_key);

        create index if not exists ix_ai_external_action_providers_provider_type
            on ai_external_action_providers (provider_type);

        create index if not exists ix_ai_external_action_providers_enabled
            on ai_external_action_providers (enabled);

        create index if not exists ix_ai_external_action_providers_created_at
            on ai_external_action_providers (created_at);
        """,
    ),

    Migration(
        "020_external_action_schemas_table",
        "Cria tabela de schemas OpenAPI importados",
        """
        create table if not exists ai_external_action_schemas (
            id uuid primary key default gen_random_uuid(),
            provider_id uuid not null references ai_external_action_providers(id) on delete cascade,
            schema_json jsonb not null,
            schema_hash varchar(128) not null,
            source_type varchar(20) not null,
            source_url text null,
            imported_at timestamptz not null default now()
        );
        """,
    ),

    Migration(
        "021_external_action_schemas_columns",
        "Atualiza colunas de schemas OpenAPI",
        """
        alter table ai_external_action_schemas
            add column if not exists source_url text null,
            add column if not exists imported_at timestamptz not null default now();
        """,
    ),

    Migration(
        "022_external_action_schemas_indexes",
        "Cria índices de schemas OpenAPI",
        """
        create index if not exists ix_ai_external_action_schemas_provider_id
            on ai_external_action_schemas (provider_id);

        create index if not exists ix_ai_external_action_schemas_schema_hash
            on ai_external_action_schemas (schema_hash);

        create index if not exists ix_ai_external_action_schemas_imported_at
            on ai_external_action_schemas (imported_at);
        """,
    ),

    Migration(
        "030_external_actions_table",
        "Cria tabela global de rotas/actions importadas",
        """
        create table if not exists ai_external_actions (
            id uuid primary key default gen_random_uuid(),
            provider_id uuid not null references ai_external_action_providers(id) on delete cascade,
            action_id varchar(220) not null unique,
            operation_id varchar(180) null,
            method varchar(10) not null,
            path text not null,
            summary text null,
            description text null,
            tags jsonb null,
            parameters_schema jsonb null,
            request_body_schema jsonb null,
            response_schema jsonb null,
            sensitivity varchar(30) not null default 'read',
            enabled boolean not null default true,
            deprecated boolean not null default false,
            created_at timestamptz not null default now(),
            updated_at timestamptz not null default now()
        );
        """,
    ),

    Migration(
        "031_external_actions_columns",
        "Atualiza colunas de rotas/actions importadas",
        """
        alter table ai_external_actions
            add column if not exists operation_id varchar(180) null,
            add column if not exists summary text null,
            add column if not exists description text null,
            add column if not exists tags jsonb null,
            add column if not exists parameters_schema jsonb null,
            add column if not exists request_body_schema jsonb null,
            add column if not exists response_schema jsonb null,
            add column if not exists sensitivity varchar(30) not null default 'read',
            add column if not exists enabled boolean not null default true,
            add column if not exists deprecated boolean not null default false,
            add column if not exists created_at timestamptz not null default now(),
            add column if not exists updated_at timestamptz not null default now();
        """,
    ),

    Migration(
        "032_external_actions_indexes",
        "Cria índices de rotas/actions importadas",
        """
        create index if not exists ix_ai_external_actions_provider_id
            on ai_external_actions (provider_id);

        create unique index if not exists ix_ai_external_actions_action_id
            on ai_external_actions (action_id);

        create index if not exists ix_ai_external_actions_operation_id
            on ai_external_actions (operation_id);

        create index if not exists ix_ai_external_actions_method
            on ai_external_actions (method);

        create index if not exists ix_ai_external_actions_sensitivity
            on ai_external_actions (sensitivity);

        create index if not exists ix_ai_external_actions_enabled
            on ai_external_actions (enabled);

        create index if not exists ix_ai_external_actions_deprecated
            on ai_external_actions (deprecated);

        create index if not exists ix_ai_external_actions_created_at
            on ai_external_actions (created_at);
        """,
    ),

    Migration(
        "040_chat_agent_action_providers_table",
        "Cria tabela de vínculo agente -> provider/action",
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
            updated_at timestamptz not null default now()
        );
        """,
    ),

    Migration(
        "041_chat_agent_action_providers_columns",
        "Atualiza colunas do vínculo agente -> provider/action",
        """
        alter table ai_chat_agent_action_providers
            add column if not exists enabled boolean not null default true,
            add column if not exists allow_read boolean not null default true,
            add column if not exists allow_write boolean not null default false,
            add column if not exists allow_admin boolean not null default false,
            add column if not exists requires_confirmation_for_write boolean not null default true,
            add column if not exists created_at timestamptz not null default now(),
            add column if not exists updated_at timestamptz not null default now();
        """,
    ),

    Migration(
        "042_chat_agent_action_providers_constraints",
        "Garante constraint única agente/provider",
        """
        do $$
        begin
            if not exists (
                select 1
                from pg_constraint
                where conname = 'uq_ai_chat_agent_action_providers_agent_provider'
            ) then
                alter table ai_chat_agent_action_providers
                    add constraint uq_ai_chat_agent_action_providers_agent_provider
                    unique (agent_id, provider_key);
            end if;
        end $$;
        """,
    ),

    Migration(
        "043_chat_agent_action_providers_indexes",
        "Cria índices do vínculo agente -> provider/action",
        """
        create index if not exists ix_ai_chat_agent_action_providers_agent_id
            on ai_chat_agent_action_providers (agent_id);

        create index if not exists ix_ai_chat_agent_action_providers_provider_key
            on ai_chat_agent_action_providers (provider_key);

        create index if not exists ix_ai_chat_agent_action_providers_enabled
            on ai_chat_agent_action_providers (enabled);
        """,
    ),

    Migration(
        "050_chat_agent_actions_table",
        "Cria tabela de overrides de rotas/actions por agente",
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
    ),

    Migration(
        "051_chat_agent_actions_columns",
        "Atualiza colunas de overrides de rotas/actions por agente",
        """
        alter table ai_chat_agent_actions
            add column if not exists provider_key varchar(120) not null default '',
            add column if not exists action_id varchar(300) not null default '',
            add column if not exists enabled boolean not null default true,
            add column if not exists sensitivity varchar(40) not null default 'read',
            add column if not exists requires_confirmation boolean not null default false,
            add column if not exists created_at timestamptz not null default now(),
            add column if not exists updated_at timestamptz not null default now();
        """,
    ),

    Migration(
        "052_chat_agent_actions_indexes",
        "Cria índices de overrides de rotas/actions por agente",
        """
        create index if not exists ix_ai_chat_agent_actions_agent_id
            on ai_chat_agent_actions (agent_id);

        create index if not exists ix_ai_chat_agent_actions_enabled
            on ai_chat_agent_actions (enabled);

        create index if not exists ix_ai_chat_agent_actions_provider_key
            on ai_chat_agent_actions (provider_key);

        create index if not exists ix_ai_chat_agent_actions_action_id
            on ai_chat_agent_actions (action_id);
        """,
    ),
]


CHECK_TABLES = [
    "ai_chat_agents",
    "ai_external_action_providers",
    "ai_external_action_schemas",
    "ai_external_actions",
    "ai_chat_agent_action_providers",
    "ai_chat_agent_actions",
]


CHECK_COLUMNS = [
    ("ai_external_action_providers", "privacy_policy_url"),
    ("ai_external_action_providers", "auth_mode"),
    ("ai_external_action_providers", "auth_config"),
    ("ai_external_action_providers", "enabled"),
    ("ai_external_action_schemas", "schema_json"),
    ("ai_external_action_schemas", "schema_hash"),
    ("ai_external_actions", "parameters_schema"),
    ("ai_external_actions", "request_body_schema"),
    ("ai_external_actions", "response_schema"),
    ("ai_external_actions", "sensitivity"),
    ("ai_external_actions", "deprecated"),
    ("ai_chat_agent_action_providers", "allow_read"),
    ("ai_chat_agent_action_providers", "allow_write"),
    ("ai_chat_agent_action_providers", "allow_admin"),
    ("ai_chat_agent_action_providers", "requires_confirmation_for_write"),
    ("ai_chat_agent_actions", "provider_key"),
    ("ai_chat_agent_actions", "action_id"),
    ("ai_chat_agent_actions", "requires_confirmation"),
]


def _table_exists(table_name: str) -> bool:
    exists = db.session.execute(
        db.text("select to_regclass(:table_name)"),
        {"table_name": f"public.{table_name}"},
    ).scalar()

    return bool(exists)


def _column_exists(table_name: str, column_name: str) -> bool:
    exists = db.session.execute(
        db.text(
            """
            select 1
            from information_schema.columns
            where table_schema = 'public'
              and table_name = :table_name
              and column_name = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar()

    return bool(exists)


def _print_state(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    print("Tabelas:")
    for table in CHECK_TABLES:
        print(f"  {table}: {'ok' if _table_exists(table) else 'missing'}")

    print("\nColunas:")
    for table, column in CHECK_COLUMNS:
        table_status = "ok" if _table_exists(table) else "missing-table"
        column_status = "ok" if table_status == "ok" and _column_exists(table, column) else "missing"
        print(f"  {table}.{column}: {column_status}")


def main() -> None:
    app = create_app()

    with app.app_context():
        if not _table_exists("ai_chat_agents"):
            raise RuntimeError(
                "Tabela base ai_chat_agents não existe. "
                "Aplique primeiro as migrations base de agentes/chat."
            )

        _print_state("Antes")

        for index, migration in enumerate(MIGRATIONS, start=1):
            print(f"\n[{index}/{len(MIGRATIONS)}] {migration.key}: {migration.description}")
            db.session.execute(db.text(migration.sql))
            db.session.flush()

        db.session.commit()

        _print_state("Depois")

        missing_tables = [table for table in CHECK_TABLES if not _table_exists(table)]
        missing_columns = [
            f"{table}.{column}"
            for table, column in CHECK_COLUMNS
            if not _column_exists(table, column)
        ]

        if missing_tables or missing_columns:
            raise RuntimeError(
                "Migrations aplicadas, mas ainda há itens faltando: "
                f"tables={missing_tables}, columns={missing_columns}"
            )

        print("\nOK: todas as migrations de chat/actions foram aplicadas.")


if __name__ == "__main__":
    main()
