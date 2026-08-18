-- Declared commercial forecast (FCT MVP) — monthly value per portfolio scope.

CREATE TABLE IF NOT EXISTS commercial.forecast_declarations (
    cycle_year      INTEGER NOT NULL,
    cycle_month     INTEGER NOT NULL,
    portfolio_id    TEXT NOT NULL DEFAULT '',
    declared_value  NUMERIC(18, 2) NOT NULL DEFAULT 0,
    updated_by      TEXT NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (cycle_year, cycle_month, portfolio_id),
    CONSTRAINT forecast_declarations_month_ck CHECK (cycle_month BETWEEN 1 AND 12)
);

COMMENT ON TABLE commercial.forecast_declarations IS
    'Declared FCT (not TOTVS, not deliveryHorizon). Empty portfolio_id = consolidado do escopo.';
