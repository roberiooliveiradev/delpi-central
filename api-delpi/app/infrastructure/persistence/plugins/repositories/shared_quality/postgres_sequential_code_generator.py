# app/infrastructure/persistence/plugins/repositories/shared_quality/postgres_sequential_code_generator.py
from __future__ import annotations

from app.domain.ports.shared_quality.sequential_code_generator import (
    SequentialCodeGeneratorPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)


class PostgresSequentialCodeGenerator(
    PluginBaseRepository,
    SequentialCodeGeneratorPort,
):
    def next_code(self, sequence_key: str) -> str:
        row = self.execute_returning_one(
            """
            UPDATE quality.document_sequences
               SET current_value = current_value + 1
             WHERE sequence_key = %s
               AND active = TRUE
         RETURNING prefix, current_value, padding_length
            """,
            (sequence_key,),
            auto_commit=True,
        )

        if not row:
            raise PluginsRepositoryError(
                f"Sequência não encontrada ou inativa: {sequence_key}"
            )

        prefix = row["prefix"]
        current_value = int(row["current_value"])
        padding_length = int(row["padding_length"])

        return f"{prefix}-{str(current_value).zfill(padding_length)}"