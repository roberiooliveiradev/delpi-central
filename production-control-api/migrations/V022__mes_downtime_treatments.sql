BEGIN;

-- PC-MES-DOWNTIME-TREATMENT — triagem e tratamento gerencial de paradas MES.
--
-- Complementa downtime_events (fato operacional canônico) com o registro
-- gerencial 1:1: análise da parada, causa (confirmada ou hipótese), decisão
-- de tratamento e vínculo rastreável com a solicitação encaminhada ao
-- requests-api (type "process-issue"). O lifecycle da solicitação NÃO é
-- duplicado aqui — guardamos apenas o vínculo (request_id + type_code) e o
-- instante da decisão; o status vivo é consultado no requests-api.
--
-- Concorrência: a coluna updated_at é o token otimista — o cliente devolve
-- o valor lido e o UPDATE condicional falha se outra escrita ocorreu no
-- intervalo.

CREATE TABLE IF NOT EXISTS production_control.mes_downtime_treatments (
    -- Identidade = a própria parada (1:1, uma triagem por ocorrência).
    downtime_id         UUID        NOT NULL
        REFERENCES production_control.downtime_events(id),
    branch              VARCHAR(2)  NOT NULL CHECK (branch IN ('01', '02')),
    work_center         VARCHAR(40) NOT NULL,

    -- Triagem: análise registrada, natureza da causa e decisão.
    analysis            TEXT        NOT NULL CHECK (btrim(analysis) <> ''),
    cause_kind          VARCHAR(20) NOT NULL
        CHECK (cause_kind IN ('confirmed', 'hypothesis')),
    cause_note          TEXT,
    action_needed       BOOLEAN     NOT NULL,
    justification       TEXT        NOT NULL CHECK (btrim(justification) <> ''),

    -- Estado do tratamento: pending → referred | concluded.
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'referred', 'concluded')),

    -- Vínculo com solicitação externa (requests-api). O tipo é guardado
    -- para rastreio mesmo que o status não possa ser lido depois.
    request_id          UUID,
    request_type_code   VARCHAR(80),
    linked_at           TIMESTAMPTZ,
    linked_by_ref       VARCHAR(120),
    linked_by_name      VARCHAR(160),

    -- Encerramento do tratamento (justificativa obrigatória).
    conclusion_reason   TEXT,
    concluded_at        TIMESTAMPTZ,
    concluded_by_ref    VARCHAR(120),
    concluded_by_name   VARCHAR(160),

    created_by_ref      VARCHAR(120) NOT NULL,
    created_by_name     VARCHAR(160) NOT NULL,
    updated_by_ref      VARCHAR(120) NOT NULL,
    updated_by_name     VARCHAR(160) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (downtime_id),

    -- Vínculo coerente: referência só existe quando encaminhado.
    CHECK ((request_id IS NULL) = (request_type_code IS NULL)),
    CHECK (request_id IS NULL OR status IN ('referred', 'concluded')),
    -- Conclusão exige instante e justificativa.
    CHECK ((concluded_at IS NULL) = (conclusion_reason IS NULL))
);

CREATE INDEX IF NOT EXISTS ix_mes_downtime_treatments_status
    ON production_control.mes_downtime_treatments (branch, status);

COMMENT ON TABLE production_control.mes_downtime_treatments IS
    'Triagem/tratamento gerencial de paradas MES (1:1 com downtime_events), com vínculo rastreável para solicitações requests-api.';

COMMIT;
