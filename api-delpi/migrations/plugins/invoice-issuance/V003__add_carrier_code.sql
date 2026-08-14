-- Invoice issuance — código SA4 da transportadora (opcional)
-- Aplicar somente com `up`. Nunca editar V001/V002.

ALTER TABLE invoice_issuance.invoice_issuance_requests
    ADD COLUMN IF NOT EXISTS carrier_code VARCHAR(6);

COMMENT ON COLUMN invoice_issuance.invoice_issuance_requests.carrier_code IS
    'Código da transportadora TOTVS (SA4.A4_COD), quando selecionada no wizard.';
