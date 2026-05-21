from __future__ import annotations

from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsRefreshStateRepository(PluginBaseRepository):
    def mark_started(self) -> None:
        self.execute(
            """
            INSERT INTO strategic_indicators.refresh_state (id, last_started_at, updated_at)
            VALUES ('default', NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                last_started_at = NOW(),
                last_error = NULL,
                updated_at = NOW()
            """
        )

    def mark_completed(
        self,
        *,
        duration_ms: int,
        periods_upserted: int,
    ) -> None:
        self.execute(
            """
            UPDATE strategic_indicators.refresh_state
            SET
                last_completed_at = NOW(),
                last_duration_ms = %s,
                last_periods_upserted = %s,
                last_error = NULL,
                updated_at = NOW()
            WHERE id = 'default'
            """,
            (duration_ms, periods_upserted),
        )

    def mark_failed(self, *, error_message: str) -> None:
        self.execute(
            """
            UPDATE strategic_indicators.refresh_state
            SET
                last_error = %s,
                updated_at = NOW()
            WHERE id = 'default'
            """,
            (error_message[:2000],),
        )
